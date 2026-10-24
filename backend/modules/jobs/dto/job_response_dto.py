from rest_framework import serializers

from modules.jobs.models import Job


class JobResponseDTO(serializers.ModelSerializer):
    min_years = serializers.DecimalField(max_digits=5, decimal_places=2, coerce_to_string=False, allow_null=True)
    max_years = serializers.DecimalField(max_digits=5, decimal_places=2, coerce_to_string=False, allow_null=True)

    class Meta:
        model = Job
        fields = [
            'id',
            'url',
            'secondary_url',
            'referral_status',
            'status',
            'company_name',
            'title',
            'official_id',
            'description',
            'location',
            'min_years',
            'max_years',
            'notes',
            'created_at',
            'updated_at',
            'score',
            'analysis',
            'is_custom_resume_generated',
            'resume_data',
        ]
