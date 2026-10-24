import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import {
  createJob,
  deleteJob,
  generateResumeForJob,
  generateResumes,
  markToApplyAsApplied,
  triggerJobScoring,
  triggerScraperPipeline,
  updateJob,
} from '../../../common/api/jobs/jobs.service';
import { extractErrorMessage } from '../../../common/utils/error.utils';
import type {
  JobCreateRequest,
  JobUpdateRequest,
} from '../interfaces/job.interfaces';

interface UpdateMutationArgs {
  id: number;
  payload: JobUpdateRequest;
}

interface BulkUpdateMutationArgs {
  ids: number[];
  payload: JobUpdateRequest;
}

export function useJobMutations() {
  const queryClient = useQueryClient();
  const invalidateJobs = () =>
    queryClient.invalidateQueries({ queryKey: ['jobs'] });

  const createMutation = useMutation({
    mutationFn: (payload: JobCreateRequest) => createJob(payload),
    onSuccess: () => {
      invalidateJobs();
      toast.success('Job added');
    },
    onError: (error) =>
      toast.error(extractErrorMessage(error) ?? 'Failed to add job'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: UpdateMutationArgs) => updateJob(id, payload),
    onSuccess: () => {
      invalidateJobs();
      toast.success('Job updated');
    },
    onError: (error) =>
      toast.error(extractErrorMessage(error) ?? 'Failed to update job'),
  });

  const bulkUpdateMutation = useMutation({
    mutationFn: ({ ids, payload }: BulkUpdateMutationArgs) =>
      Promise.all(ids.map((id) => updateJob(id, payload))),
    onSuccess: () => {
      invalidateJobs();
      toast.success('Jobs updated');
    },
    onError: (error) =>
      toast.error(extractErrorMessage(error) ?? 'Failed to update jobs'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteJob(id),
    onSuccess: () => {
      invalidateJobs();
      toast.success('Job deleted');
    },
    onError: (error) =>
      toast.error(extractErrorMessage(error) ?? 'Failed to delete job'),
  });

  const generateResumesMutation = useMutation({
    mutationFn: () => generateResumes(),
    onSuccess: (result) => {
      if (result.queued) {
        toast.success(result.message);
      } else {
        toast(result.message);
      }
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error) ?? 'Failed to queue resume generation');
    },
  });

  const triggerJobScoringMutation = useMutation({
    mutationFn: () => triggerJobScoring(),
    onSuccess: (result) => {
      if (result.queued) {
        toast.success(result.message);
      } else {
        toast(result.message);
      }
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error) ?? 'Failed to queue job scoring');
    },
  });

  const markToApplyAsAppliedMutation = useMutation({
    mutationFn: () => markToApplyAsApplied(),
    onSuccess: (result) => {
      invalidateJobs();
      toast.success(`Marked ${result.updatedCount} job(s) as Applied`);
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error) ?? 'Failed to mark jobs as Applied');
    },
  });

  const fetchLatestJobsMutation = useMutation({
    mutationFn: ({ scraperNames, runScoring }: { scraperNames?: string[]; runScoring?: boolean }) =>
      triggerScraperPipeline(scraperNames, runScoring),
    onSuccess: (result) => {
      if (result.queued) {
        toast.success(result.message);
      } else {
        toast(result.message);
      }
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error) ?? 'Failed to queue scraper run');
    },
  });

  const buildResumeMutation = useMutation({
    mutationFn: (jobId: number) => generateResumeForJob(jobId),
    onSuccess: (result) => {
      if (result.queued) {
        toast.success(result.message);
      } else {
        toast(result.message);
      }
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error) ?? 'Failed to queue resume generation');
    },
  });

  return {
    createMutation,
    updateMutation,
    bulkUpdateMutation,
    deleteMutation,
    generateResumesMutation,
    buildResumeMutation,
    fetchLatestJobsMutation,
    triggerJobScoringMutation,
    markToApplyAsAppliedMutation,
  };
}
