from django_q.tasks import async_task

from common.utils.notification_manager import NotificationManager
from modules.ai.services.claude_cli_service import run_claude_skill
from modules.resume.services.resume_generation_service import generate_resumes_for_pending_jobs

JOB_SCORING_TASK_GROUP = 'job_scoring'
JOB_SCORING_SKILL_COMMAND = '/job-scoring'


def run_job_scoring() -> None:
    """Runs the job-scoring skill (which scores every Pending job via the API and
    persists the results itself) then, once it succeeds, queues resume generation for
    whichever jobs now qualify."""
    try:
        run_claude_skill(JOB_SCORING_SKILL_COMMAND)
    except Exception as error:
        NotificationManager.show('Job scoring failed', str(error))
        raise
    NotificationManager.show('Job scoring complete', 'Job scoring finished successfully.')
    generate_resumes_for_pending_jobs()


def trigger_job_scoring() -> dict:
    async_task('modules.ai_scoring.tasks.run_job_scoring_task', group=JOB_SCORING_TASK_GROUP)
    return {'queued': True, 'message': 'Job scoring started.'}
