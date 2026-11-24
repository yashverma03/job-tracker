from django_q.tasks import async_task

from common.utils.notification_manager import NotificationManager
from modules.ai.services.claude_cli_service import run_claude_skill
from modules.resume.services.resume_generation_service import (
    RESUME_GENERATION_SKILL_COMMAND,
    has_jobs_pending_resume_generation,
)

JOB_SCORING_TASK_GROUP = 'job_scoring'
JOB_SCORING_SKILL_COMMAND = '/job-scoring'


def run_job_scoring() -> None:
    """Runs the job-scoring skill (which scores every Pending job via the API and
    persists the results itself) then, once it succeeds, resume generation for whichever
    jobs now qualify, with a single notification covering both steps."""
    NotificationManager.run_with_notification('Job scoring and resume generation', _score_and_generate_resumes)


def _score_and_generate_resumes() -> None:
    run_claude_skill(JOB_SCORING_SKILL_COMMAND)
    if has_jobs_pending_resume_generation():
        run_claude_skill(RESUME_GENERATION_SKILL_COMMAND)


def trigger_job_scoring() -> dict:
    async_task('modules.ai_scoring.tasks.run_job_scoring_task', group=JOB_SCORING_TASK_GROUP)
    return {'queued': True, 'message': 'Job scoring started.'}
