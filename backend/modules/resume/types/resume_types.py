from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict


class ResumeContact(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str
    title: str
    portfolio_url: str
    resume_url: str
    email: str
    phone: str
    linkedin_url: str
    github_url: str
    gfg_url: str
    leetcode_url: str


class ResumeExperienceEntry(BaseModel):
    model_config = ConfigDict(extra='forbid')

    title: str
    company: str
    duration: str
    base_bullets: list[str]


class ResumeCertification(BaseModel):
    model_config = ConfigDict(extra='forbid')

    label: str
    url: str


class ResumeEducation(BaseModel):
    model_config = ConfigDict(extra='forbid')

    degree: str
    institution: str
    years: str


class ResumeInput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    contact: ResumeContact
    years_of_experience: float
    min_experience_years: float
    max_experience_years: float
    expected_ctc_lpa: float
    shortlist_cap: int
    base_summary: str
    skills_summary: str
    experience: list[ResumeExperienceEntry]
    skills: list[str]
    certifications: list[ResumeCertification]
    education: list[ResumeEducation]


@dataclass
class ResumeContent:
    summary: str
    experience_bullets: list[list[str]]
    skills: list[str]


@dataclass
class ResumeGenerationOutcome:
    job_id: int
    file_path: str | None = None
    reason: str | None = None
    error: str | None = None
