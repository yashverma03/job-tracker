import axios from 'axios';

import { API_BASE_URL } from '../../configs/api.config';
import type {
  GenerateResumesQueuedResponse,
  JobCreateRequest,
  JobListQueryParams,
  JobListResponse,
  JobResponse,
  JobStatsResponse,
  JobUpdateRequest,
  ScraperNameOption,
  ScraperPipelineQueuedResponse,
} from '../../../modules/jobs/interfaces/job.interfaces';

const client = axios.create({
  baseURL: API_BASE_URL,
  paramsSerializer: { indexes: null },
});

export async function fetchJobs(
  params: JobListQueryParams,
): Promise<JobListResponse> {
  const { data } = await client.get<JobListResponse>('/jobs', { params });
  return data;
}

export async function createJob(
  payload: JobCreateRequest,
): Promise<JobResponse> {
  const { data } = await client.post<JobResponse>('/jobs', payload);
  return data;
}

export async function updateJob(
  id: number,
  payload: JobUpdateRequest,
): Promise<JobResponse> {
  const { data } = await client.patch<JobResponse>(`/jobs/${id}`, payload);
  return data;
}

export async function deleteJob(id: number): Promise<void> {
  await client.delete(`/jobs/${id}`);
}

export async function generateResumes(): Promise<GenerateResumesQueuedResponse> {
  const { data } = await client.post<GenerateResumesQueuedResponse>('/resumes');
  return data;
}

export async function triggerJobScoring(): Promise<ScraperPipelineQueuedResponse> {
  const { data } = await client.post<ScraperPipelineQueuedResponse>('/job-scoring');
  return data;
}

export async function markToApplyAsApplied(): Promise<{ updatedCount: number }> {
  const { data } = await client.patch<{ updatedCount: number }>(
    '/jobs/mark-to-apply-applied',
  );
  return data;
}

export async function generateResumeForJob(
  jobId: number,
): Promise<GenerateResumesQueuedResponse> {
  const { data } = await client.post<GenerateResumesQueuedResponse>(
    `/resumes/${jobId}`,
  );
  return data;
}

export async function fetchCompanyNames(
  search?: string,
  limit?: number,
): Promise<string[]> {
  const { data } = await client.get<string[]>('/jobs/company-names', {
    params: { search, limit },
  });
  return data;
}

export async function fetchJobTitles(
  search?: string,
  limit?: number,
): Promise<string[]> {
  const { data } = await client.get<string[]>('/jobs/job-titles', {
    params: { search, limit },
  });
  return data;
}

export async function fetchJobStats(): Promise<JobStatsResponse> {
  const { data } = await client.get<JobStatsResponse>('/jobs/stats');
  return data;
}

export async function triggerScraperPipeline(
  scraperNames?: string[],
  runScoring = false,
): Promise<ScraperPipelineQueuedResponse> {
  const { data } = await client.post<ScraperPipelineQueuedResponse>('/scraper', {
    scraperNames,
    runScoring,
  });
  return data;
}

export async function fetchScraperNameOptions(): Promise<ScraperNameOption[]> {
  const { data } = await client.get<ScraperNameOption[]>('/scraper');
  return data;
}

export async function fetchCompanyNameByUrl(
  url: string,
): Promise<string | null> {
  const { data } = await client.get<{ companyName: string | null }>(
    '/jobs/company-by-url',
    {
      params: { url },
    },
  );
  return data.companyName;
}
