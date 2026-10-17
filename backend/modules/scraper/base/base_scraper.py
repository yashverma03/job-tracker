import json
import threading
from abc import ABC, abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor, wait as wait_futures
from dataclasses import replace

from curl_cffi.requests.exceptions import HTTPError

from common.exceptions.api_exceptions import ApiError
from common.utils.env import get_env_int
from modules.company.services import company_service
from modules.jobs.enums.job_referral_status import JobReferralStatus
from modules.jobs.enums.job_status import JobStatus
from modules.jobs.services import job_service, job_unique_key_service
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.types import ListingPage, ScraperJobData, ScraperRunResult
from modules.scraper.utils.job_filter import is_location_excluded, is_title_excluded
from modules.scraper.utils.scraper_logger import get_scraper_logger

REQUIRED_JOB_FIELDS = ('url', 'title', 'company_name', 'location', 'description')
DETAIL_WORKER_COUNT_ENV_KEY = 'SCRAPER_DETAIL_WORKER_COUNT'

# Kept short so a large HTML error/challenge page doesn't blow up the log line.
ERROR_BODY_LOG_LIMIT = 2000


def _format_http_error(exc: HTTPError, status_code: int | None, body: str | None) -> str:
    truncated_body = body[:ERROR_BODY_LOG_LIMIT] if body else body
    return f'{exc} | status={status_code} body={truncated_body!r}'


class BaseScraper(ABC):
    """Shared orchestration for every scraper strategy: pagination, the two-stage
    exclusion filter, concurrent detail fetching, and persistence all live here so a
    new scraper only has to implement the handful of methods below it - everything
    else (dedup, filtering, threading, error bookkeeping, final validation, insert) is
    common business logic and must not be duplicated per scraper.

    Pipeline for each run:
      1. `_fetch_listing_page` is called repeatedly to page through candidate jobs.
      2. Each listing is checked by `_passes_pre_detail_filter` *before* any detail
         request is made, so excluded jobs never cost an extra HTTP call.
      3. Listings that pass are handed to the detail worker pool: `_fetch_detail_fields`
         fills in whatever only the detail page can provide (typically the
         description), the exclusion filter runs again now that those fields are
         known, then a final compulsory-field check runs immediately before insert.
    """

    def __init__(self):
        self._logger = get_scraper_logger(self.name)
        self._state_lock = threading.Lock()
        self._total_count = 0
        self._total_unique_count = 0
        self._errors: list[dict] = []

    @property
    def detail_worker_count(self) -> int:
        """Shared worker-pool size for concurrent job-detail fetches, every scraper
        strategy reads the same env-configured value."""
        return get_env_int(DETAIL_WORKER_COUNT_ENV_KEY)

    @property
    @abstractmethod
    def name(self) -> ScraperName:
        """Unique identifier for this scraper, matches the value stored in scraper_runs.name."""

    @property
    @abstractmethod
    def page_size(self) -> int:
        """Number of listings requested per page; used to advance the pagination offset."""

    @abstractmethod
    def _fetch_listing_page(self, start: int, time_range_hours: int) -> ListingPage:
        """Fetch and parse one page of candidate jobs starting at `start`, applying any
        listing-level filtering only the scraper itself can do (e.g. a posted-date
        cutoff). Set `ListingPage.stop=True` once pagination should end (e.g. an empty
        page, or a scraper-specific threshold like too many consecutive empty pages).

        `time_range_hours` is a LinkedIn-only concept (its search API takes a posted-
        within-window param); every other scraper should ignore it (prefix the
        parameter with `_` to signal that) rather than implementing a time cutoff."""

    @abstractmethod
    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        """Fetch whatever fields require a per-job detail request - typically just
        `description` - returned as a dict of field name -> value to merge onto the
        listing. Only called for listings that already passed the pre-detail filter, so
        implementations can assume the request is actually needed."""

    def close(self) -> None:
        """Releases any resources the scraper acquired for this run (e.g. a browser
        process for a Playwright-driven scraper). No-op by default; the caller is
        responsible for calling this exactly once per instance, after `run()` finishes
        (success or failure)."""

    def _reset_run_state(self) -> None:
        self._total_count = 0
        self._total_unique_count = 0
        self._errors = []

    def _listing_json(self, listing: ScraperJobData) -> str:
        return json.dumps(
            {
                'url': listing.url,
                'title': listing.title,
                'company_name': listing.company_name,
                'location': listing.location,
                'official_id': listing.official_id,
            }
        )

    def _record_error(self, url: str | None, message: str) -> None:
        self._logger.warning('job processing failed for %s: %s', url, message)
        with self._state_lock:
            self._errors.append({'url': url, 'message': message})

    def current_metadata(self) -> dict:
        """Snapshot of run progress so far - same shape as the metadata `run()` returns
        on completion. Lets a caller persist partial progress (e.g. counts at the point
        the process was killed) instead of losing it."""
        with self._state_lock:
            return {
                'total_count': self._total_count,
                'total_unique_count': self._total_unique_count,
                'error_count': len(self._errors),
            }

    def run(self, max_jobs_per_run: int, start_offset: int, time_range_hours: int) -> ScraperRunResult:
        """Page through listings, filter, then fetch details concurrently for anything
        worth fetching. Identical across every scraper - only the abstract hooks above
        vary per source.

        `max_jobs_per_run` is a hard cap on raw listings pulled from the list API
        (tracked by `_total_count`), enforced here regardless of `_fetch_listing_page`'s
        own pagination-end logic - a last-resort bound so a scraper-specific pagination
        bug (or a source that never reports "no more pages") can't page through an
        unbounded number of listings. Exclusion filtering happens only within that
        budget, same as before."""
        self._reset_run_state()
        start = start_offset
        pending: list[Future] = []

        with ThreadPoolExecutor(
            max_workers=self.detail_worker_count, thread_name_prefix=f'{self.name.value}-detail'
        ) as executor:
            while self._total_count < max_jobs_per_run:
                self._logger.info('fetching listing page start=%s', start)
                try:
                    page = self._fetch_listing_page(start, time_range_hours)
                except HTTPError as exc:
                    status_code = exc.response.status_code if exc.response is not None else None
                    body = exc.response.text if exc.response is not None else None
                    if status_code is not None and (status_code in (400, 404) or status_code >= 500):
                        self._logger.warning(
                            'stopping pagination, listing page failed with %s, body=%s', exc, body
                        )
                        break
                    raise HTTPError(_format_http_error(exc, status_code, body)) from exc

                remaining_budget = max_jobs_per_run - self._total_count
                listings = page.listings[:remaining_budget]
                self._total_count += len(listings)

                for listing in listings:
                    if self._passes_pre_detail_filter(listing):
                        pending.append(executor.submit(self._process_listing, listing))

                start += self.page_size

                if page.stop:
                    self._logger.info('stopping pagination')
                    break

                if len(listings) < len(page.listings):
                    self._logger.info('stopping pagination, reached max_jobs_per_run=%s', max_jobs_per_run)
                    break

            wait_futures(pending)
            for future in pending:
                future.result()  # surface any unexpected (non-per-job) exception

        self._logger.info(
            'run complete, fetched=%s inserted=%s errors=%s',
            self._total_count,
            self._total_unique_count,
            len(self._errors),
        )

        return ScraperRunResult(metadata=self.current_metadata(), errors=self._errors)

    def _passes_pre_detail_filter(self, listing: ScraperJobData) -> bool:
        """First-pass filter, applied before spending an HTTP request on the job's
        detail page: de-duplication plus the exclusion rules over whatever fields the
        listing page already gave us. A field the listing page doesn't provide (e.g. a
        source that only reveals location on the detail page) simply can't exclude the
        job yet - the same rules run again in `_process_listing` once the detail
        response has filled the gaps, and a final compulsory-field check runs right
        before insert."""
        if job_unique_key_service.is_duplicate(listing.url, None):
            self._logger.info('excluded by filter rule (duplicate url): %s', self._listing_json(listing))
            return False

        exclusion_reason = self.get_exclusion_reason(listing.title, listing.location, listing.company_name)
        if exclusion_reason:
            self._logger.info('excluded (%s): %s', exclusion_reason, self._listing_json(listing))
            self._insert_excluded_job(listing, exclusion_reason)
            return False

        return True

    def _process_listing(self, listing: ScraperJobData) -> None:
        """Runs on the detail worker pool for every listing that passed the pre-detail
        filter: fetches the scraper-specific detail fields, re-applies the exclusion
        filter now that those fields are available, does a final compulsory-field
        check, then persists the job. Only one scraper-specific call happens here
        (`_fetch_detail_fields`) - everything else is shared."""
        try:
            self._logger.info('fetching details for %s', listing.url)
            detail_fields = self._fetch_detail_fields(listing)
            listing = replace(listing, **detail_fields)

            exclusion_reason = self.get_exclusion_reason(listing.title, listing.location, listing.company_name)
            if exclusion_reason:
                self._logger.info('excluded (%s): %s', exclusion_reason, self._listing_json(listing))
                self._insert_excluded_job(listing, exclusion_reason)
                return

            missing_fields = [field for field in REQUIRED_JOB_FIELDS if not getattr(listing, field)]
            if missing_fields:
                self._record_error(
                    listing.url, f'missing required fields: {", ".join(missing_fields)} | {self._listing_json(listing)}'
                )
                return

            job_service.create_scraped_job(
                title=listing.title,
                company_name=listing.company_name,
                location=listing.location,
                description=listing.description,
                url=listing.url,
                referral_status=self.get_referral_status_for_company(listing.company_name),
                official_id=listing.official_id,
            )
        except ApiError as exc:
            duplicate_reason = self._duplicate_reason(exc)
            if duplicate_reason:
                self._logger.info('skipped duplicate job (%s): %s', duplicate_reason, self._listing_json(listing))
                return
            self._record_error(listing.url, str(exc))
            return
        except HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            body = exc.response.text if exc.response is not None else None
            self._record_error(listing.url, _format_http_error(exc, status_code, body))
            return
        except Exception as exc:  # noqa: BLE001 - one job's failure must not abort the run
            self._record_error(listing.url, str(exc))
            return

        with self._state_lock:
            self._total_unique_count += 1
        self._logger.info('job inserted: %s', listing.url)

    def _duplicate_reason(self, exc: ApiError) -> str | None:
        if str(exc) == 'A job with this URL already exists.':
            return 'duplicate url'
        if str(exc) == 'A job with this company and official ID already exists.':
            return 'duplicate company + official id'
        return None

    def _insert_excluded_job(self, listing: ScraperJobData, exclusion_reason: str) -> None:
        try:
            job_service.create_scraped_job(
                title=listing.title,
                company_name=listing.company_name,
                location=listing.location,
                description=listing.description,
                url=listing.url,
                referral_status=self.get_referral_status_for_company(listing.company_name),
                official_id=listing.official_id,
                status=JobStatus.NOT_RELEVANT,
                analysis=exclusion_reason,
            )
        except ApiError as exc:
            duplicate_reason = self._duplicate_reason(exc)
            if duplicate_reason:
                self._logger.info(
                    'skipped duplicate excluded job (%s): %s', duplicate_reason, self._listing_json(listing)
                )
                return
            self._record_error(listing.url, str(exc))
        except Exception as exc:  # noqa: BLE001 - one job's failure must not abort the run
            self._record_error(listing.url, str(exc))

    def get_exclusion_reason(self, title: str | None, location: str | None, company_name: str | None) -> str | None:
        """Shared pre-insert filter every scraper strategy should apply: excluded role
        titles, out-of-scope locations, blacklisted companies, and companies still in
        their cooling-off period. Returns the name of the rule that excluded the job,
        or None if it passes every rule."""
        if is_title_excluded(title):
            return 'Filter Rule: title not allowed'
        if is_location_excluded(location):
            return 'Filter Rule: location not allowed'
        if company_service.is_blacklisted(company_name):
            return 'Filter Rule: company blacklisted'
        if company_service.is_in_cooling_period(company_name):
            return 'Filter Rule: company in cooling period'
        if company_service.is_covered_by_other_scraper(company_name, self.name.value):
            return 'Filter Rule: company has dedicated scraper'
        return None

    def get_referral_status_for_company(self, company_name: str | None) -> str:
        # if company_service.is_top_company(company_name):
        #     return JobReferralStatus.REQUIRED
        return JobReferralStatus.NOT_ASKING
