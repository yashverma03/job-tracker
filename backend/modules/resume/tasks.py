from common.utils.notification_manager import NotificationManager
from modules.jobs.models import Job
from modules.resume.services.resume_generation_service import process_job
from modules.resume.utils.resume_input_loader import load_resume_input
from modules.resume.utils.resume_log import log_resume_batch_result, log_resume_progress


def run_resume_generation_batch_task(job_ids: list[int], output_dir: str) -> None:
    resume_input = load_resume_input()
    jobs_by_id = Job.objects.in_bulk(job_ids)
    jobs = [jobs_by_id[job_id] for job_id in job_ids if job_id in jobs_by_id]

    outcomes = []
    for index, job in enumerate(jobs, start=1):
        outcome = process_job(job, resume_input, output_dir)
        outcomes.append(outcome)
        log_resume_progress(index, len(jobs), outcome)

    generated = [outcome for outcome in outcomes if outcome.error is None]
    failed = [outcome for outcome in outcomes if outcome.error is not None]

    log_resume_batch_result(total=len(jobs), generated=generated, failed=failed)
    NotificationManager.show(
        'Resume generation complete',
        f'Total: {len(jobs)}\nSuccess: {len(generated)}\nFailed: {len(failed)}',
    )
