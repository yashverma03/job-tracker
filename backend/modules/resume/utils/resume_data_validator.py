from modules.resume.types.resume_types import ResumeInput
from modules.resume.utils.resume_constants import (
    RESUME_BULLET_MAX_CHARS,
    RESUME_BULLET_MAX_COUNT,
    RESUME_BULLET_MIN_CHARS,
    RESUME_BULLET_MIN_COUNT,
    RESUME_MAX_SKILLS,
    RESUME_SKILL_MAX_CHARS,
    RESUME_SUMMARY_MAX_CHARS,
    RESUME_SUMMARY_MIN_CHARS,
)

BOLD_MARKER = '**'


def _visible_length(text: str) -> int:
    return len(text.replace(BOLD_MARKER, ''))


def validate_resume_data(
    summary: str, experience_bullets: list[list[str]], skills: list[str], resume_input: ResumeInput
) -> list[str]:
    """Returns every length/count violation at once, so the caller can fix them all in a single retry."""
    errors = []

    if not RESUME_SUMMARY_MIN_CHARS <= len(summary) <= RESUME_SUMMARY_MAX_CHARS:
        errors.append(
            f'summary is {len(summary)} characters; it must be {RESUME_SUMMARY_MIN_CHARS}-{RESUME_SUMMARY_MAX_CHARS}.'
        )

    entries = resume_input.experience
    if len(experience_bullets) != len(entries):
        errors.append(
            f'experienceBullets has {len(experience_bullets)} entries; it must have exactly {len(entries)} '
            '(one array per experience entry, in the same order).'
        )
    else:
        for index, (entry, bullets) in enumerate(zip(entries, experience_bullets)):
            label = f'experienceBullets[{index}] ({entry.title} at {entry.company})'
            if not RESUME_BULLET_MIN_COUNT <= len(bullets) <= RESUME_BULLET_MAX_COUNT:
                errors.append(
                    f'{label} has {len(bullets)} bullets; it must have {RESUME_BULLET_MIN_COUNT}-{RESUME_BULLET_MAX_COUNT}.'
                )
            for bullet_index, bullet in enumerate(bullets, start=1):
                length = _visible_length(bullet)
                if not RESUME_BULLET_MIN_CHARS <= length <= RESUME_BULLET_MAX_CHARS:
                    errors.append(
                        f'{label} bullet {bullet_index} is {length} characters; '
                        f'it must be {RESUME_BULLET_MIN_CHARS}-{RESUME_BULLET_MAX_CHARS}.'
                    )

    if not 1 <= len(skills) <= RESUME_MAX_SKILLS:
        errors.append(f'skills has {len(skills)} entries; it must have 1-{RESUME_MAX_SKILLS}.')
    for skill in skills:
        if len(skill) > RESUME_SKILL_MAX_CHARS:
            errors.append(f'skill "{skill}" is {len(skill)} characters; it must be at most {RESUME_SKILL_MAX_CHARS}.')

    return errors
