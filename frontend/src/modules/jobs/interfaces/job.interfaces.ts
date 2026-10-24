import type { PaginatedResponse } from '../../../common/types/api.types';
import type { Job, JobReferralStatus, JobStatus } from '../types/job.types';

export type JobResponse = Job;

export type JobListResponse = PaginatedResponse<JobResponse>;

export interface JobCreateRequest {
  url?: string;
  secondaryUrl?: string;
  companyName?: string;
  title?: string;
  officialId?: string;
  description?: string;
  location?: string;
  notes?: string;
  status?: JobStatus;
  referralStatus?: JobReferralStatus;
  score?: number | null;
  analysis?: string | null;
}

export type JobUpdateRequest = Partial<JobCreateRequest>;

export interface JobListQueryParams {
  status?: JobStatus[];
  referralStatus?: JobReferralStatus[];
  dateFrom?: string;
  dateTo?: string;
  search?: string;
  page: number;
  limit: number;
}

export interface JobStatsResponse {
  toApplyCount: number;
  referralRequiredCount: number;
  pendingJobsCount: number;
}

export interface GenerateResumesQueuedResponse {
  queued: boolean;
  processing: number;
  message: string;
}

export interface ScraperPipelineQueuedResponse {
  queued: boolean;
  message: string;
}

export interface ScraperNameOption {
  value: string;
  label: string;
}

export interface JobFormValues {
  url: string;
  secondaryUrl: string;
  companyName: string;
  title: string;
  officialId: string;
  description: string;
  location: string;
  notes: string;
  status: JobStatus;
  referralStatus: JobReferralStatus;
  score: string;
  analysis: string;
}
