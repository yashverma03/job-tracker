import { useMemo, useState } from 'react';

import { useUrlSearchParams } from '../../../common/hooks/useUrlSearchParams';
import { JobsFilters } from './JobsFilters';
import { JobsTable } from './JobsTable';
import { BulkActionsBar } from './BulkActionsBar';
import { JobFormModal, type JobCloneSource } from './JobFormModal';
import { AddMultipleJobsModal } from './AddMultipleJobsModal';
import { ScraperSelectModal } from './ScraperSelectModal';
import { useJobMutations } from '../hooks/useJobMutations';
import { useJobsQuery } from '../hooks/useJobsQuery';
import { useJobStatsQuery } from '../hooks/useJobStatsQuery';
import {
  buildSearchParams,
  parseFiltersFromSearchParams,
  parseModeFromSearchParams,
} from '../utils/filterParams.utils';
import type {
  JobListQueryParams,
  JobUpdateRequest,
} from '../interfaces/job.interfaces';
import type { Job, JobsViewMode } from '../types/job.types';
import styles from './JobsPage.module.css';

export function JobsPage() {
  const [searchParams, setSearchParams] = useUrlSearchParams();
  const filters = useMemo(
    () => parseFiltersFromSearchParams(searchParams),
    [searchParams],
  );
  const mode = useMemo(
    () => parseModeFromSearchParams(searchParams),
    [searchParams],
  );

  const setFilters = (
    updater: JobListQueryParams | ((prev: JobListQueryParams) => JobListQueryParams),
  ) => {
    const next =
      typeof updater === 'function' ? updater(filters) : updater;
    setSearchParams(buildSearchParams(next, mode));
  };

  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [cloneSource, setCloneSource] = useState<JobCloneSource | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isAddMultipleOpen, setIsAddMultipleOpen] = useState(false);
  const [isScraperSelectOpen, setIsScraperSelectOpen] = useState(false);

  const { data, isLoading, isError } = useJobsQuery(filters);
  const { data: stats } = useJobStatsQuery();
  const {
    createMutation,
    updateMutation,
    deleteMutation,
    generateResumesMutation,
    buildResumeMutation,
    fetchLatestJobsMutation,
    triggerJobScoringMutation,
    markToApplyAsAppliedMutation,
  } = useJobMutations();

  const jobs = useMemo(() => data?.items ?? [], [data]);
  const totalPages = data
    ? Math.max(1, Math.ceil(data.total / data.pageSize))
    : 1;

  const selectedJobs = useMemo(
    () => jobs.filter((job) => selectedIds.has(job.id)),
    [jobs, selectedIds],
  );

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const openAddForm = () => {
    setEditingJob(null);
    setCloneSource(null);
    setIsFormOpen(true);
  };

  const openEditForm = (job: Job) => {
    setEditingJob(job);
    setCloneSource(null);
    setIsFormOpen(true);
  };

  const openCloneForm = (job: Job) => {
    setEditingJob(null);
    setCloneSource({
      companyName: job.companyName,
      title: job.title,
      status: job.status,
      referralStatus: job.referralStatus,
    });
    setIsFormOpen(true);
  };

  const closeForm = () => {
    setIsFormOpen(false);
    setCloneSource(null);
  };

  const handleDelete = (job: Job) => {
    deleteMutation.mutate(job.id, { onSuccess: closeForm });
  };

  const handleGenerateResume = (job: Job) => {
    buildResumeMutation.mutate(job.id);
  };

  const handleFormSubmit = (payload: JobUpdateRequest) => {
    if (editingJob) {
      updateMutation.mutate(
        { id: editingJob.id, payload },
        { onSuccess: closeForm },
      );
    } else {
      createMutation.mutate(payload, { onSuccess: closeForm });
    }
  };

  const handleModeChange = (newMode: JobsViewMode) => {
    const next: JobListQueryParams = { ...filters, page: 1 };
    delete next.status;
    delete next.referralStatus;
    if (newMode === 'apply') {
      next.status = ['To Apply'];
    } else if (newMode === 'referral') {
      next.referralStatus = ['Referral required'];
    }
    setSearchParams(buildSearchParams(next, newMode));
  };

  const goToPage = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const resetFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <button
          type="button"
          className={styles.title}
          onClick={resetFilters}
        >
          Job Tracker
        </button>
        <div className={styles.headerButtons}>
          <button
            type="button"
            className={styles.addButton}
            onClick={openAddForm}
          >
            <span className={styles.addButtonIcon} aria-hidden="true">
              +
            </span>
            Add Job
          </button>
        </div>
      </div>

      <div className={styles.toolbar}>
        <button
          type="button"
          className={styles.markToApplyAppliedButton}
          disabled={markToApplyAsAppliedMutation.isPending}
          onClick={() => markToApplyAsAppliedMutation.mutate()}
        >
          {markToApplyAsAppliedMutation.isPending
            ? 'Marking...'
            : 'Mark To Apply as Applied'}
        </button>
        <button
          type="button"
          className={styles.fetchLatestJobsButton}
          disabled={fetchLatestJobsMutation.isPending}
          onClick={() => setIsScraperSelectOpen(true)}
        >
          {fetchLatestJobsMutation.isPending ? 'Queuing...' : 'Get Latest Jobs'}
        </button>
        <button
          type="button"
          className={styles.generateResumesButton}
          disabled={triggerJobScoringMutation.isPending}
          onClick={() => triggerJobScoringMutation.mutate()}
        >
          {triggerJobScoringMutation.isPending
            ? 'Queuing...'
            : 'Score & Generate Resumes'}
        </button>
        <button
          type="button"
          className={styles.generateResumesButton}
          disabled={generateResumesMutation.isPending}
          onClick={() => generateResumesMutation.mutate()}
        >
          {generateResumesMutation.isPending
            ? 'Queuing...'
            : 'Generate Custom Resumes'}
        </button>
      </div>

      <JobsFilters
        filters={filters}
        onChange={setFilters}
        mode={mode}
        onModeChange={handleModeChange}
      />

      <div className={styles.statsBarSlot}>
        {selectedJobs.length < 2 && (
          <div className={styles.stats}>
            <span className={styles.statPill}>
              To Apply: {stats?.toApplyCount ?? '—'}
            </span>
            <span className={styles.statPill}>
              Referral required: {stats?.referralRequiredCount ?? '—'}
            </span>
            <span className={styles.statPill}>
              Pending jobs: {stats?.pendingJobsCount ?? '—'}
            </span>
          </div>
        )}
        <BulkActionsBar selectedJobs={selectedJobs} />
      </div>

      {isLoading && <p className={styles.statusText}>Loading jobs...</p>}
      {isError && <p className={styles.errorText}>Failed to load jobs.</p>}

      {!isLoading && !isError && (
        <>
          <JobsTable
            jobs={jobs}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onEdit={openEditForm}
            onDelete={handleDelete}
            onClone={openCloneForm}
            mode={mode}
          />

          <div className={styles.pagination}>
            <span>
              Page {filters.page} of {totalPages} ({data?.total ?? 0} jobs)
            </span>
            <div className={styles.paginationButtons}>
              <button
                type="button"
                className={styles.pageButton}
                disabled={filters.page <= 1}
                onClick={() => goToPage(filters.page - 1)}
              >
                Previous
              </button>
              <button
                type="button"
                className={styles.pageButton}
                disabled={filters.page >= totalPages}
                onClick={() => goToPage(filters.page + 1)}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}

      {isFormOpen && (
        <JobFormModal
          job={editingJob}
          cloneFrom={cloneSource}
          onClose={closeForm}
          onSubmit={handleFormSubmit}
          onDelete={handleDelete}
          onGenerateResume={handleGenerateResume}
          isGeneratingResume={buildResumeMutation.isPending}
        />
      )}

      {isAddMultipleOpen && (
        <AddMultipleJobsModal onClose={() => setIsAddMultipleOpen(false)} />
      )}

      {isScraperSelectOpen && (
        <ScraperSelectModal
          isSubmitting={fetchLatestJobsMutation.isPending}
          onClose={() => setIsScraperSelectOpen(false)}
          onConfirm={(scraperNames, runScoring) => {
            fetchLatestJobsMutation.mutate(
              { scraperNames: scraperNames.length > 0 ? scraperNames : undefined, runScoring },
              { onSuccess: () => setIsScraperSelectOpen(false) },
            );
          }}
        />
      )}
    </div>
  );
}
