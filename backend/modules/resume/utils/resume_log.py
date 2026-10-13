from datetime import datetime

from modules.resume.types.resume_types import ResumeGenerationOutcome
from modules.resume.utils.resume_constants import RESUME_LOG_PATH


def _write(line: str) -> None:
    with open(RESUME_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def log_resume_progress(index: int, total: int, outcome: ResumeGenerationOutcome) -> None:
    timestamp = datetime.now().isoformat(sep=' ', timespec='seconds')
    if outcome.file_path is None:
        status, detail = 'failed', outcome.error
    elif outcome.reason is not None:
        status, detail = 'skipped', f'{outcome.file_path} ({outcome.reason})'
    else:
        status, detail = 'success', outcome.file_path
    _write(
        f'[{timestamp}] job {index} of {total} done — job_id={outcome.job_id} status={status} detail={detail}',
    )


def log_resume_batch_result(
    total: int,
    generated: list[ResumeGenerationOutcome],
    failed: list[ResumeGenerationOutcome],
) -> None:
    timestamp = datetime.now().isoformat(sep=' ', timespec='seconds')
    _write(f'[{timestamp}] BATCH SUMMARY total={total} success={len(generated)} failed={len(failed)}')
