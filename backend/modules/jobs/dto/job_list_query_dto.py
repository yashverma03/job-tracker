from rest_framework import serializers

from modules.jobs.enums.job_referral_status import JobReferralStatus
from modules.jobs.enums.job_status import JobStatus
from modules.jobs.types.job_types import JobFilterParams


class OptionalBooleanField(serializers.BooleanField):
    default_empty_html = serializers.empty


class JobListQueryDTO(serializers.Serializer):
    status = serializers.ListField(
        child=serializers.ChoiceField(choices=JobStatus.choices),
        required=False,
        allow_null=True,
        allow_empty=True,
    )
    referral_status = serializers.ListField(
        child=serializers.ChoiceField(choices=JobReferralStatus.choices),
        required=False,
        allow_null=True,
        allow_empty=True,
    )
    date_from = serializers.DateField(required=False, allow_null=True)
    date_to = serializers.DateField(required=False, allow_null=True)
    search = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_custom_resume_generated = OptionalBooleanField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    limit = serializers.IntegerField(min_value=1)

    def to_filter_params(self) -> JobFilterParams:
        data: dict = self.validated_data  # type: ignore[assignment]
        return JobFilterParams(
            page=data.get('page', 1),
            limit=data['limit'],
            status=data.get('status'),
            referral_status=data.get('referral_status'),
            date_from=data.get('date_from'),
            date_to=data.get('date_to'),
            search=data.get('search'),
            is_custom_resume_generated=data.get('is_custom_resume_generated'),
        )
