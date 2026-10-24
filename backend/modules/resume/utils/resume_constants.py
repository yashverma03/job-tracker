from common.utils.env import get_env

DEFAULT_RESUME_PATH = get_env('DEFAULT_RESUME_PATH')

# Below this many characters of cleaned job description text, there isn't enough signal to meaningfully
# tailor a resume, so the default resume is used as-is instead of tailoring one.
MIN_JOB_DESCRIPTION_LENGTH_FOR_AI = 50

# These platforms don't accept custom resumes, so jobs hosted on them always use the default resume.
DEFAULT_RESUME_ONLY_DOMAINS = ('wellfound.com',)

# Length limits for tailored resume data (1 rendered line is 110 characters); they keep the resume on one page.
RESUME_SUMMARY_MIN_CHARS = 111
RESUME_SUMMARY_MAX_CHARS = 220
RESUME_BULLET_MIN_COUNT = 1
RESUME_BULLET_MAX_COUNT = 5
RESUME_BULLET_MIN_CHARS = 30
RESUME_BULLET_MAX_CHARS = 220
RESUME_MAX_SKILLS = 20
RESUME_SKILL_MAX_CHARS = 40
