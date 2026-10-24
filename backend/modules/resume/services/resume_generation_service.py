import os
import shutil
from urllib.parse import urlparse

from django_q.models import Task
from django_q.tasks import async_task

from common.exceptions.api_exceptions import ApiError
from common.utils.env import get_env
from modules.ai.utils.ai_log import log_ai_call
from modules.jobs.enums.job_status import JobStatus
from modules.jobs.models import Job
from modules.jobs.services.job_service import list_jobs
from modules.jobs.types.job_types import JobFilterParams
from modules.resume.services.resume_pdf_service import render_resume_pdf
from modules.resume.types.resume_types import ResumeContent, ResumeGenerationOutcome, ResumeInput
from modules.resume.utils.resume_constants import (
    DEFAULT_RESUME_ONLY_DOMAINS,
    DEFAULT_RESUME_PATH,
    MIN_JOB_DESCRIPTION_LENGTH_FOR_AI,
)
from modules.resume.utils.resume_input_loader import load_resume_input
from modules.resume.utils.text_cleaner import clean_job_description

RESUME_GENERATION_TASK_GROUP = 'resume_generation'
RESUME_GENERATION_SKILL_COMMAND = '/job-resume-generation'
MAX_ELIGIBLE_JOBS = 10000


def _resume_filename(resume_input: ResumeInput, job_id: int) -> str:
    name_slug = '_'.join(word.capitalize() for word in resume_input.contact.name.split())
    return f'{name_slug}_Resume_{job_id}.pdf'


def _eligible_job_count() -> int:
    filters = JobFilterParams(
        page=1,
        limit=MAX_ELIGIBLE_JOBS,
        status=[JobStatus.TO_APPLY],
        is_custom_resume_generated=False,
        has_description=True,
    )
    return list_jobs(filters).total


def _generation_in_progress() -> bool:
    return Task.objects.filter(group=RESUME_GENERATION_TASK_GROUP, stopped__isnull=True).exists()


def _mark_resume_generated(job: Job) -> None:
    job.is_custom_resume_generated = True
    job.save(update_fields=['is_custom_resume_generated'])


def _uses_default_resume_only(job: Job) -> bool:
    hostname = (urlparse(job.url or '').hostname or '').lower()
    return any(hostname == domain or hostname.endswith(f'.{domain}') for domain in DEFAULT_RESUME_ONLY_DOMAINS)


def _stored_resume_content(job: Job) -> ResumeContent:
    data = job.resume_data
    if not data:
        raise ApiError('Resume content has not been generated for this job yet.', status_code=400)
    return ResumeContent(
        summary=data['summary'],
        experience_bullets=data['experience_bullets'],
        skills=data['skills'],
    )


def process_job(job: Job, resume_input: ResumeInput, output_dir: str) -> ResumeGenerationOutcome:
    if _uses_default_resume_only(job):
        _mark_resume_generated(job)
        return ResumeGenerationOutcome(job_id=job.pk, reason='Platform does not accept custom resumes; skipped.')

    file_path = os.path.join(output_dir, _resume_filename(resume_input, job.pk))

    if len(clean_job_description(job.description or '')) < MIN_JOB_DESCRIPTION_LENGTH_FOR_AI:
        os.makedirs(output_dir, exist_ok=True)
        shutil.copyfile(DEFAULT_RESUME_PATH, file_path)
        _mark_resume_generated(job)
        return ResumeGenerationOutcome(
            job_id=job.pk,
            file_path=file_path,
            reason='Job description too short to tailor; used default resume.',
        )

    try:
        render_resume_pdf(resume_input, _stored_resume_content(job), file_path)
    except ApiError:
        raise
    except Exception as exc:  # noqa: BLE001
        return ResumeGenerationOutcome(job_id=job.pk, error=str(exc))

    _mark_resume_generated(job)
    return ResumeGenerationOutcome(job_id=job.pk, file_path=file_path)


def generate_resumes_for_pending_jobs() -> dict:
    if _generation_in_progress():
        return {'queued': False, 'processing': 0, 'message': 'A resume generation run is already in progress.'}

    job_count = _eligible_job_count()

    if not job_count:
        return {'queued': False, 'processing': 0, 'message': 'No jobs pending resume generation.'}

    async_task('modules.resume.tasks.run_resume_generation_task', group=RESUME_GENERATION_TASK_GROUP)

    return {
        'queued': True,
        'processing': job_count,
        'message': f'Resume generation queued for {job_count} job(s).',
    }


def _get_job_with_description(job_id: int) -> Job:
    job = Job.objects.filter(deleted_at__isnull=True, id=job_id).first()
    if job is None:
        raise ApiError(f'Job {job_id} not found', status_code=404)

    if not job.description or not job.description.strip():
        raise ApiError('Job description is required to generate a resume.', status_code=400)

    return job


def queue_resume_generation_for_job(job_id: int) -> dict:
    _get_job_with_description(job_id)

    if _generation_in_progress():
        return {'queued': False, 'processing': 0, 'message': 'A resume generation run is already in progress.'}

    async_task('modules.resume.tasks.run_resume_generation_task', job_id, group=RESUME_GENERATION_TASK_GROUP)

    return {'queued': True, 'processing': 1, 'message': f'Resume generation queued for job {job_id}.'}


def render_resume_pdf_for_job(job_id: int) -> ResumeGenerationOutcome:
    job = _get_job_with_description(job_id)
    resume_input = load_resume_input()
    output_dir = get_env('RESUME_OUTPUT_DIR')

    try:
        outcome = process_job(job, resume_input, output_dir)
    except ApiError as exc:
        log_ai_call(f'RESUME PDF FAILED job_id={job_id} error={exc}')
        raise

    if outcome.error is not None:
        log_ai_call(f'RESUME PDF FAILED job_id={job_id} error={outcome.error}')
    else:
        log_ai_call(f'RESUME PDF OK job_id={job_id} file={outcome.file_path} note={outcome.reason or "-"}')

    return outcome


def get_resume_file_path(job_id: int) -> str:
    resume_input = load_resume_input()
    output_dir = get_env('RESUME_OUTPUT_DIR')
    return os.path.join(output_dir, _resume_filename(resume_input, job_id))
