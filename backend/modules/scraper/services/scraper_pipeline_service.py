import os
import signal
import threading
from concurrent.futures import ThreadPoolExecutor

from django_q.tasks import async_task

from common.utils.env import get_env_int
from common.utils.notification_manager import NotificationManager
from modules.ai_scoring.services.job_scoring_service import trigger_job_scoring
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.scrapers.registry import get_enabled_scrapers
from modules.scraper.services import scraper_run_service
from modules.scraper.types import ScraperRunOutcome
from modules.scraper.utils.scraper_logger import get_scraper_logger

SCRAPER_PIPELINE_TASK_GROUP = 'scraper_pipeline'

MAX_JOBS_PER_RUN_ENV_KEY = 'SCRAPER_MAX_JOBS_PER_RUN'
START_OFFSET_ENV_KEY = 'SCRAPER_START_OFFSET'
TIME_RANGE_HOURS_ENV_KEY = 'SCRAPER_TIME_RANGE_HOURS'
CONCURRENT_SCRAPER_LIMIT_ENV_KEY = 'SCRAPER_CONCURRENT_LIMIT'

# The whole pipeline now runs as a single Django-Q task, with every scraper running
# concurrently on its own thread inside that one task (each scraper in turn runs its own
# detail-fetch thread pool, so this is threads-within-threads by design). Signal handling
# therefore has to track every currently-running scraper, not just one - keyed by the
# thread running it, guarded by a lock since scrapers report in/out from their own
# threads while the signal handler (always invoked on the main thread) reads the set.
_active_runs: dict[int, tuple] = {}
_active_runs_lock = threading.Lock()

# SIGKILL can't be caught by any process, so a `kill -9` can never be recovered from
# here - these are the signals a terminated terminal/process actually sends
# (Ctrl+C, `kill`, closing the terminal).
_TERMINATION_SIGNALS = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)


def _handle_termination_signal(signum: int, frame) -> None:
    with _active_runs_lock:
        contexts = list(_active_runs.values())

    if not contexts:
        os._exit(1)

    signal_name = signal.Signals(signum).name
    for run, scraper, logger in contexts:
        logger.error('run finished: Failed - process terminated by signal %s', signal_name)
        scraper_run_service.mark_failed(
            run,
            error={'message': f'process terminated ({signal_name})'},
            metadata=scraper.current_metadata(),
        )
    os._exit(1)


def run_scraper(scraper: BaseScraper, max_jobs_per_run: int, start_offset: int, time_range_hours: int) -> ScraperRunOutcome:
    """Run a single scraper end-to-end (its own run record and status transitions).
    Runs on its own thread within the pipeline's thread pool so scrapers execute
    concurrently instead of one after another."""
    logger = get_scraper_logger(scraper.name)

    run = scraper_run_service.create_pending_run(scraper.name)
    logger.info('run started: run_id=%s', run.id)

    active_run_key = threading.get_ident()
    with _active_runs_lock:
        _active_runs[active_run_key] = (run, scraper, logger)

    try:
        scraper_run_service.mark_processing(run)
        logger.info('run marked Processing')

        result = scraper.run(max_jobs_per_run, start_offset, time_range_hours)
        metadata = result.metadata
        errors = result.errors

        if errors:
            scraper_run_service.mark_failed(
                run,
                error={'message': f'{len(errors)} job(s) failed during the run.', 'errors': errors},
                metadata=metadata,
            )
            logger.error('run finished: Failed error_count=%s', len(errors))
            return ScraperRunOutcome(scraper.name, status='failed', **metadata)

        scraper_run_service.mark_success(run, metadata=metadata)
        logger.info('run finished: Success')
        return ScraperRunOutcome(scraper.name, status='success', **metadata)
    except Exception as exc:  # noqa: BLE001 - one scraper's failure must not abort others
        metadata = scraper.current_metadata()
        scraper_run_service.mark_failed(run, {'message': str(exc)}, metadata=metadata)
        logger.error('run finished: Failed error=%s', exc)
        return ScraperRunOutcome(scraper.name, status='failed', **metadata)
    finally:
        with _active_runs_lock:
            _active_runs.pop(active_run_key, None)
        scraper.close()


def run_scraper_pipeline(
    scraper_names: list[str] | None,
    max_jobs_per_run: int,
    start_offset: int,
    time_range_hours: int,
    run_scoring: bool = False,
    init_only: bool = False,
) -> None:
    """Runs every requested scraper concurrently (bounded by
    `SCRAPER_CONCURRENT_LIMIT`), waits for all of them to finish, then shows a single
    notification summarizing how many succeeded/failed/were skipped and how many jobs
    each added. This is the single Django-Q task queued per pipeline trigger."""
    if init_only and scraper_run_service.has_run_today():
        return

    scrapers = get_enabled_scrapers()
    if scraper_names is not None:
        scrapers = [scraper for scraper in scrapers if scraper.name in scraper_names]

    concurrent_limit = get_env_int(CONCURRENT_SCRAPER_LIMIT_ENV_KEY)

    previous_handlers = {sig: signal.signal(sig, _handle_termination_signal) for sig in _TERMINATION_SIGNALS}
    try:
        with ThreadPoolExecutor(max_workers=concurrent_limit, thread_name_prefix='scraper-pipeline') as executor:
            futures = [
                executor.submit(run_scraper, scraper, max_jobs_per_run, start_offset, time_range_hours)
                for scraper in scrapers
            ]
            outcomes = [future.result() for future in futures]
    finally:
        for sig, previous_handler in previous_handlers.items():
            signal.signal(sig, previous_handler)

    _notify_pipeline_summary(outcomes)

    if run_scoring and outcomes and all(outcome.status == 'success' for outcome in outcomes):
        trigger_job_scoring()


def _notify_pipeline_summary(outcomes: list[ScraperRunOutcome]) -> None:
    rows = [
        [
            outcome.scraper_name.label,
            outcome.total_count,
            outcome.total_unique_count,
            outcome.error_count,
            outcome.status.capitalize(),
        ]
        for outcome in sorted(outcomes, key=lambda outcome: outcome.scraper_name.label)
    ]
    rows.append(
        [
            'Total',
            sum(outcome.total_count for outcome in outcomes),
            sum(outcome.total_unique_count for outcome in outcomes),
            sum(outcome.error_count for outcome in outcomes),
            '',
        ]
    )

    NotificationManager.show_table(
        'Scraper pipeline complete',
        ['Name', 'Total Count', 'Added', 'Failed', 'Status'],
        rows,
        width=900,
        height=600,
    )


def trigger_scraper_pipeline(
    scraper_names: list[str] | None = None, init_only: bool = False, run_scoring: bool = False
) -> dict:
    """`scraper_names`, if given, restricts the run to just those scrapers (matched
    against `ScraperName` values) - None/omitted runs every registered scraper, same as
    before this parameter existed.

    `init_only` restricts triggering to once per day overall: if a scraper pipeline run
    already exists for today, the call is a no-op. Intended for the daily cron trigger,
    so re-triggering it (e.g. after a machine restart) doesn't queue a second run.

    `run_scoring` controls whether job scoring runs after a fully successful pipeline
    run. Defaults to False; the daily cron trigger sets it to True.
    """
    if init_only and scraper_run_service.has_run_today():
        return {'queued': False, 'message': 'A scraper pipeline run already exists for today.'}

    max_jobs_per_run = get_env_int(MAX_JOBS_PER_RUN_ENV_KEY)
    start_offset = get_env_int(START_OFFSET_ENV_KEY)
    time_range_hours = get_env_int(TIME_RANGE_HOURS_ENV_KEY)

    async_task(
        'modules.scraper.tasks.run_scraper_pipeline_task',
        scraper_names,
        max_jobs_per_run,
        start_offset,
        time_range_hours,
        run_scoring,
        init_only,
        group=SCRAPER_PIPELINE_TASK_GROUP,
    )

    return {'queued': True, 'message': 'Scraper pipeline started.'}
