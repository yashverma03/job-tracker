from django.db import models
from django.db.models.functions import Now

from modules.jobs.enums.job_referral_status import JobReferralStatus
from modules.jobs.enums.job_status import JobStatus


class Job(models.Model):
    url = models.TextField(null=True, blank=True)
    secondary_url = models.TextField(null=True, blank=True)
    referral_status = models.TextField(
        choices=JobReferralStatus.choices,
        default=JobReferralStatus.NOT_ASKING,
    )
    status = models.TextField(
        choices=JobStatus.choices,
        default=JobStatus.TO_APPLY,
    )
    company_name = models.TextField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    official_id = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    min_years = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_years = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    analysis = models.TextField(null=True, blank=True)
    is_custom_resume_generated = models.BooleanField(default=False)
    resume_data = models.JSONField(null=True, blank=True)
    is_manual_created = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'jobs'
        indexes = [
            models.Index(fields=['status'], name='job_status_idx'),
            models.Index(fields=['referral_status'], name='job_referral_status_idx'),
            models.Index(fields=['company_name'], name='job_company_name_idx'),
            models.Index(fields=['official_id'], name='job_official_id_idx'),
            models.Index(fields=['title'], name='job_title_idx'),
        ]

    def __str__(self):
        return f'{self.title or "Untitled"} @ {self.company_name or "Unknown"}'
