from rest_framework import serializers

from modules.jobs.dto.validators import validate_years_range
from modules.jobs.enums.job_referral_status import JobReferralStatus
from modules.jobs.enums.job_status import JobStatus
from modules.jobs.models import Job
from modules.resume.utils.resume_data_validator import validate_resume_data
from modules.resume.utils.resume_input_loader import load_resume_input


class ResumeDataDTO(serializers.Serializer):
    summary = serializers.CharField()
    experience_bullets = serializers.ListField(child=serializers.ListField(child=serializers.CharField()))
    skills = serializers.ListField(child=serializers.CharField())


class JobUpdateDTO(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=JobStatus.choices, required=False)
    referral_status = serializers.ChoiceField(choices=JobReferralStatus.choices, required=False)
    min_years = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False, required=False, allow_null=True
    )
    max_years = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False, required=False, allow_null=True
    )

    resume_data = ResumeDataDTO(required=False, allow_null=True)

    class Meta:
        model = Job
        fields = [
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
            'score',
            'analysis',
            'resume_data',
        ]
        extra_kwargs = {
            'url': {'required': False, 'allow_blank': True, 'allow_null': True},
            'secondary_url': {'required': False, 'allow_blank': True, 'allow_null': True},
            'score': {'required': False, 'allow_null': True},
            'analysis': {'required': False, 'allow_blank': True, 'allow_null': True},
        }

    def validate_resume_data(self, value):
        if value is None:
            return value

        summary = value['summary'].strip()
        experience_bullets = [[bullet.strip() for bullet in bullets] for bullets in value['experience_bullets']]
        skills = [skill.strip() for skill in value['skills']]

        errors = validate_resume_data(summary, experience_bullets, skills, load_resume_input())
        if errors:
            raise serializers.ValidationError(errors)

        return {'summary': summary, 'experience_bullets': experience_bullets, 'skills': skills}

    def validate(self, attrs):
        min_years = attrs.get('min_years', getattr(self.instance, 'min_years', None))
        max_years = attrs.get('max_years', getattr(self.instance, 'max_years', None))
        validate_years_range({'min_years': min_years, 'max_years': max_years})
        return attrs
