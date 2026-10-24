from common.utils.notification_manager import NotificationManager
from modules.ai.services.claude_cli_service import run_claude_skill
from modules.resume.services.resume_generation_service import RESUME_GENERATION_SKILL_COMMAND


def run_resume_generation_task(job_id: int | None = None) -> None:
    """Runs the job-resume-generation skill, which tailors resume content via the API, persists it, and triggers
    PDF generation itself. With a job_id it (re)generates just that job, otherwise every eligible job."""
    skill_command = RESUME_GENERATION_SKILL_COMMAND if job_id is None else f'{RESUME_GENERATION_SKILL_COMMAND} {job_id}'
    run_claude_skill(skill_command)
    NotificationManager.show('Resume generation complete', 'Resume generation finished successfully.')
