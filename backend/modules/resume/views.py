import os

from django.http import FileResponse, Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.resume.dto import ResumeGenerationOutcomeDTO, ResumeGenerationQueuedDTO
from modules.resume.services.resume_generation_service import (
    generate_resumes_for_pending_jobs,
    get_resume_file_path,
    queue_resume_generation_for_job,
    render_resume_pdf_for_job,
)


class GenerateResumesView(APIView):
    def post(self, request):
        result = generate_resumes_for_pending_jobs()
        status_code = 202 if result['queued'] else 200
        return Response(ResumeGenerationQueuedDTO(result).data, status=status_code)


class GenerateResumeForJobView(APIView):
    def post(self, request, job_id):
        result = queue_resume_generation_for_job(job_id)
        status_code = 202 if result['queued'] else 200
        return Response(ResumeGenerationQueuedDTO(result).data, status=status_code)


class RenderResumePdfView(APIView):
    def post(self, request, job_id):
        outcome = render_resume_pdf_for_job(job_id)
        status_code = 500 if outcome.error is not None else 200
        return Response(ResumeGenerationOutcomeDTO(outcome).data, status=status_code)


class ResumeFileView(APIView):
    def get(self, request, job_id):
        file_path = get_resume_file_path(job_id)
        if not os.path.isfile(file_path):
            raise Http404('Resume file not found.')
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
