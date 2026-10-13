from common.utils.env import get_env

RESUME_LOG_PATH = get_env('RESUME_LOG_PATH')
DEFAULT_RESUME_PATH = get_env('DEFAULT_RESUME_PATH')

# Below this many characters of cleaned job description text, there isn't enough signal to meaningfully
# tailor a resume, so the default resume is used as-is instead of calling the AI.
MIN_JOB_DESCRIPTION_LENGTH_FOR_AI = 50
