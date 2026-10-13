import os
import shutil

from django_q.models import Task
from django_q.tasks import async_task

from common.exceptions.api_exceptions import ApiError
from common.utils.env import get_env
from modules.jobs.enums.job_status import JobStatus
from modules.jobs.models import Job
from modules.jobs.services.job_service import list_jobs
from modules.jobs.types.job_types import JobFilterParams
from modules.ai.services.resume_ai_service import generate_resume_content
from modules.resume.services.resume_pdf_service import render_resume_pdf
from modules.resume.types.resume_types import ResumeGenerationOutcome, ResumeInput
from modules.resume.utils.resume_constants import DEFAULT_RESUME_PATH, MIN_JOB_DESCRIPTION_LENGTH_FOR_AI
from modules.resume.utils.resume_input_loader import load_resume_input
from modules.resume.utils.text_cleaner import clean_job_description

RESUME_BATCH_TASK_GROUP = 'resume_generation_batch'
MAX_ELIGIBLE_JOBS = 10000
MAX_RESUME_GENERATION_ATTEMPTS = 3


def _resume_filename(resume_input: ResumeInput, job_id: int) -> str:
    name_slug = '_'.join(word.capitalize() for word in resume_input.contact.name.split())
    return f'{name_slug}_Resume_{job_id}.pdf'


def _eligible_job_ids_in_priority_order() -> list[int]:
    filters = JobFilterParams(
        page=1,
        limit=MAX_ELIGIBLE_JOBS,
        status=[JobStatus.TO_APPLY],
        is_custom_resume_generated=False,
        has_description=True,
    )
    return [job.pk for job in list_jobs(filters).items]


def _batch_in_progress() -> bool:
    return Task.objects.filter(group=RESUME_BATCH_TASK_GROUP, stopped__isnull=True).exists()


def _mark_resume_generated(job: Job) -> None:
    job.is_custom_resume_generated = True
    job.save(update_fields=['is_custom_resume_generated'])


def process_job(job: Job, resume_input: ResumeInput, output_dir: str) -> ResumeGenerationOutcome:
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

    last_error: Exception | None = None

    for attempt in range(1, MAX_RESUME_GENERATION_ATTEMPTS + 1):
        try:
            ai_output = generate_resume_content(job.title or '', job.description or '', resume_input)
            render_resume_pdf(resume_input, ai_output, file_path)
            _mark_resume_generated(job)

            return ResumeGenerationOutcome(job_id=job.pk, file_path=file_path)
        except Exception as exc:  # noqa: BLE001 - one job's failure must not abort the batch
            last_error = exc

    return ResumeGenerationOutcome(job_id=job.pk, error=str(last_error))


def generate_resumes_for_pending_jobs() -> dict:
    if _batch_in_progress():
        return {'queued': False, 'processing': 0, 'message': 'A resume generation batch is already in progress.'}

    output_dir = get_env('RESUME_OUTPUT_DIR')
    job_ids = _eligible_job_ids_in_priority_order()

    if not job_ids:
        return {'queued': False, 'processing': 0, 'message': 'No jobs pending resume generation.'}

    async_task(
        'modules.resume.tasks.run_resume_generation_batch_task',
        job_ids,
        output_dir,
        group=RESUME_BATCH_TASK_GROUP,
    )

    return {
        'queued': True,
        'processing': len(job_ids),
        'message': f'Resume generation queued for {len(job_ids)} job(s).',
    }


def generate_resume_for_job(job_id: int) -> ResumeGenerationOutcome:
    job = Job.objects.filter(deleted_at__isnull=True, id=job_id).first()
    if job is None:
        raise ApiError(f'Job {job_id} not found', status_code=404)

    if not job.description or not job.description.strip():
        raise ApiError('Job description is required to generate a resume.', status_code=400)

    resume_input = load_resume_input()
    output_dir = get_env('RESUME_OUTPUT_DIR')

    return process_job(job, resume_input, output_dir)


def get_resume_file_path(job_id: int) -> str:
    resume_input = load_resume_input()
    output_dir = get_env('RESUME_OUTPUT_DIR')
    return os.path.join(output_dir, _resume_filename(resume_input, job_id))
