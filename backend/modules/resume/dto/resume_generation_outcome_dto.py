from rest_framework import serializers


class ResumeGenerationOutcomeDTO(serializers.Serializer):
    job_id = serializers.IntegerField()
    file_path = serializers.CharField(required=False, allow_null=True)
    reason = serializers.CharField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)
