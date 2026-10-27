import { Fragment, useEffect, useRef, useState } from 'react';

import dayjs from 'dayjs';
import {
  CheckCheck,
  CopyPlus,
  FileText,
  Pencil,
  RotateCw,
  Trash2,
} from 'lucide-react';

import { Dropdown } from '../../../common/components/Dropdown';
import { API_BASE_URL } from '../../../common/configs/api.config';
import { useClipboard } from '../../../common/hooks/useClipboard';
import {
  REFERRAL_STATUS_DROPDOWN_OPTIONS,
  STATUS_DROPDOWN_OPTIONS,
} from '../constants/job.constants';
import { useJobMutations } from '../hooks/useJobMutations';
import { MessageButtons } from './MessageButtons';
import type { Job, JobsViewMode } from '../types/job.types';
import styles from './JobsTable.module.css';

interface Column {
  key: keyof Job;
  label: string;
  truncate?: boolean;
  width: number;
}

const COLUMNS: Column[] = [
  { key: 'url', label: 'URL', truncate: true, width: 70 },
  { key: 'secondaryUrl', label: 'Secondary URL', truncate: true, width: 70 },
  { key: 'companyName', label: 'Company name', width: 140 },
  { key: 'title', label: 'Title', width: 160 },
  { key: 'officialId', label: 'Official ID', width: 110 },
  { key: 'description', label: 'Description', truncate: true, width: 95 },
  { key: 'location', label: 'Location', width: 100 },
  { key: 'score', label: 'Score', width: 60 },
  { key: 'analysis', label: 'Analysis', truncate: true, width: 80 },
];

function buildResumeFileUrl(jobId: number): string {
  return `${API_BASE_URL}/resumes/${jobId}/file`;
}

const CHECKBOX_COLUMN_WIDTH = 40;
const ACTIONS_COLUMN_WIDTH = 170;
const ID_COLUMN_WIDTH = 70;
const DATE_COLUMN_WIDTH = 110;
const DATE_FORMAT = 'DD MMM YYYY';
const STATUS_COLUMN_WIDTH = 170;
const REFERRAL_STATUS_COLUMN_WIDTH = 180;
const RESUME_GENERATED_COLUMN_WIDTH = 90;
const MESSAGES_COLUMN_WIDTH = 224;

interface JobsTableProps {
  jobs: Job[];
  selectedIds: Set<number>;
  onToggleSelect: (id: number) => void;
  onEdit: (job: Job) => void;
  onDelete: (job: Job) => void;
  onClone: (job: Job) => void;
  mode: JobsViewMode;
}

export function JobsTable({
  jobs,
  selectedIds,
  onToggleSelect,
  onEdit,
  onDelete,
  onClone,
  mode,
}: JobsTableProps) {
  const showStatusColumn = mode !== 'referral';
  const showReferralColumn = mode !== 'apply';
  const { copy } = useClipboard();
  const { updateMutation, buildResumeMutation } = useJobMutations();

  const tableScrollRef = useRef<HTMLDivElement>(null);
  const bottomScrollRef = useRef<HTMLDivElement>(null);
  const tableRef = useRef<HTMLTableElement>(null);
  const isSyncingScroll = useRef(false);
  const [tableWidth, setTableWidth] = useState(0);

  useEffect(() => {
    const tableEl = tableRef.current;
    if (!tableEl) return;

    setTableWidth(tableEl.scrollWidth);

    const resizeObserver = new ResizeObserver(() =>
      setTableWidth(tableEl.scrollWidth),
    );
    resizeObserver.observe(tableEl);
    return () => resizeObserver.disconnect();
  }, [jobs]);

  const syncScroll = (
    source: HTMLDivElement,
    target: HTMLDivElement | null,
  ) => {
    if (isSyncingScroll.current || !target) return;
    isSyncingScroll.current = true;
    target.scrollLeft = source.scrollLeft;
    isSyncingScroll.current = false;
  };

  const handleStatusChange = (job: Job, status: string) => {
    updateMutation.mutate({
      id: job.id,
      payload: { status: status as Job['status'] },
    });
  };

  const handleReferralStatusChange = (job: Job, referralStatus: string) => {
    updateMutation.mutate({
      id: job.id,
      payload: { referralStatus: referralStatus as Job['referralStatus'] },
    });
  };

  return (
    <div className={styles.tableContainer}>
      <div
        className={styles.tableWrapper}
        ref={tableScrollRef}
        onScroll={(event) =>
          syncScroll(event.currentTarget, bottomScrollRef.current)
        }
      >
        <table className={styles.table} ref={tableRef}>
          <thead className={styles.thead}>
            <tr>
              <th
                className={`${styles.th} ${styles.checkboxCell}`}
                style={{ width: CHECKBOX_COLUMN_WIDTH }}
              />
              <th
                className={`${styles.th} ${styles.actionsCell}`}
                style={{ width: ACTIONS_COLUMN_WIDTH }}
              >
                Actions
              </th>
              <th
                className={`${styles.th} ${styles.cellWrap}`}
                style={{ width: DATE_COLUMN_WIDTH }}
              >
                Date
              </th>
              {showStatusColumn && (
                <th
                  className={`${styles.th} ${styles.cellTruncate}`}
                  style={{ width: STATUS_COLUMN_WIDTH }}
                >
                  Job Status
                </th>
              )}
              {showReferralColumn && (
                <th
                  className={`${styles.th} ${styles.cellTruncate}`}
                  style={{ width: REFERRAL_STATUS_COLUMN_WIDTH }}
                >
                  Referral status
                </th>
              )}
              <th
                className={`${styles.th} ${styles.cellWrap}`}
                style={{ width: ID_COLUMN_WIDTH }}
              >
                ID
              </th>
              {COLUMNS.map((column) => (
                <Fragment key={column.key}>
                  <th
                    className={`${styles.th} ${column.truncate ? styles.cellTruncate : styles.cellWrap}`}
                    style={{ width: column.width }}
                  >
                    {column.label}
                  </th>
                  {column.key === 'description' && (
                    <th
                      className={`${styles.th} ${styles.cellTruncate}`}
                      style={{ width: RESUME_GENERATED_COLUMN_WIDTH }}
                    >
                      Resume Generated
                    </th>
                  )}
                </Fragment>
              ))}
              <th
                className={`${styles.th} ${styles.messagesCell}`}
                style={{ width: MESSAGES_COLUMN_WIDTH }}
              >
                Messages
              </th>
            </tr>
          </thead>
          <tbody className={styles.tbody}>
            {jobs.map((job) => (
              <tr key={job.id} className={styles.row}>
                <td
                  className={styles.checkboxCell}
                  style={{ width: CHECKBOX_COLUMN_WIDTH }}
                >
                  <input
                    type="checkbox"
                    className={styles.checkbox}
                    checked={selectedIds.has(job.id)}
                    onChange={() => onToggleSelect(job.id)}
                  />
                </td>
                <td
                  className={styles.actionsCell}
                  style={{ width: ACTIONS_COLUMN_WIDTH }}
                >
                  <div className={styles.actionsRow}>
                    <button
                      type="button"
                      className={styles.editButton}
                      onClick={() => onEdit(job)}
                      aria-label="Edit job"
                    >
                      <Pencil size={16} />
                    </button>
                    <button
                      type="button"
                      className={styles.cloneButton}
                      onClick={() => onClone(job)}
                      aria-label="Clone job"
                      title="Clone job"
                    >
                      <CopyPlus size={16} />
                    </button>
                    <button
                      type="button"
                      className={styles.deleteButton}
                      onClick={() => onDelete(job)}
                      aria-label="Delete job"
                    >
                      <Trash2 size={16} />
                    </button>
                    {job.isCustomResumeGenerated ? (
                      <a
                        href={buildResumeFileUrl(job.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.viewResumeButton}
                        aria-label="View generated resume"
                        title="View generated resume"
                      >
                        <FileText size={16} />
                      </a>
                    ) : null}
                  </div>
                </td>
                <td
                  className={styles.cellWrap}
                  style={{ width: DATE_COLUMN_WIDTH }}
                >
                  {dayjs(job.createdAt).format(DATE_FORMAT)}
                </td>
                {showStatusColumn && (
                  <td
                    className={styles.cellTruncate}
                    style={{ width: STATUS_COLUMN_WIDTH }}
                  >
                    <div className={styles.statusCellInner}>
                      <Dropdown
                        label="Status"
                        hideLabel
                        value={job.status}
                        onChange={(value) => handleStatusChange(job, value)}
                        options={STATUS_DROPDOWN_OPTIONS}
                        highlighted={job.status === 'To Apply'}
                      />
                      {job.status === 'To Apply' ? (
                        <button
                          type="button"
                          className={styles.quickActionButton}
                          onClick={() => handleStatusChange(job, 'Applied')}
                          title="Mark as Applied"
                          aria-label="Mark as Applied"
                        >
                          <CheckCheck size={14} />
                        </button>
                      ) : null}
                    </div>
                  </td>
                )}
                {showReferralColumn && (
                  <td
                    className={styles.cellTruncate}
                    style={{ width: REFERRAL_STATUS_COLUMN_WIDTH }}
                  >
                    <div className={styles.statusCellInner}>
                      <Dropdown
                        label="Referral status"
                        hideLabel
                        value={job.referralStatus}
                        onChange={(value) =>
                          handleReferralStatusChange(job, value)
                        }
                        options={REFERRAL_STATUS_DROPDOWN_OPTIONS}
                        highlighted={
                          job.referralStatus === 'Referral required'
                        }
                      />
                      {job.referralStatus === 'Referral required' ? (
                        <button
                          type="button"
                          className={styles.quickActionButton}
                          onClick={() =>
                            handleReferralStatusChange(job, 'Referral asked')
                          }
                          title="Mark as Referral asked"
                          aria-label="Mark as Referral asked"
                        >
                          <CheckCheck size={14} />
                        </button>
                      ) : null}
                    </div>
                  </td>
                )}
                <td
                  className={styles.cellWrap}
                  style={{ width: ID_COLUMN_WIDTH }}
                >
                  <button
                    type="button"
                    className={styles.copyButton}
                    onClick={() => copy(String(job.id))}
                    title={String(job.id)}
                  >
                    {job.id}
                  </button>
                </td>
                {COLUMNS.map((column) => {
                  if (column.key === 'url' || column.key === 'secondaryUrl') {
                    const linkValue = job[column.key] as string | null;
                    return (
                      <td
                        key={column.key}
                        className={styles.cellTruncate}
                        style={{ width: column.width }}
                      >
                        {linkValue ? (
                          <button
                            type="button"
                            className={styles.urlButton}
                            onClick={(event) => {
                              if (event.ctrlKey || event.metaKey) {
                                window.open(
                                  linkValue,
                                  '_blank',
                                  'noopener,noreferrer',
                                );
                                return;
                              }
                              copy(linkValue);
                            }}
                            title={linkValue}
                          >
                            {linkValue}
                          </button>
                        ) : null}
                      </td>
                    );
                  }
                  const value = job[column.key];
                  const hasValue = value !== null && value !== undefined;
                  return (
                    <Fragment key={column.key}>
                      <td
                        className={
                          column.truncate
                            ? styles.cellTruncate
                            : styles.cellWrap
                        }
                        style={{ width: column.width }}
                      >
                        {hasValue ? (
                          <button
                            type="button"
                            className={styles.copyButton}
                            onClick={() => copy(String(value))}
                            title={String(value)}
                          >
                            {value}
                          </button>
                        ) : null}
                      </td>
                      {column.key === 'description' && (
                        <td
                          className={styles.cellTruncate}
                          style={{ width: RESUME_GENERATED_COLUMN_WIDTH }}
                        >
                          <div className={styles.resumeGeneratedCellInner}>
                            <span>
                              {job.isCustomResumeGenerated ? 'Yes' : 'No'}
                            </span>
                            <button
                              type="button"
                              className={styles.reloadButton}
                              onClick={() => buildResumeMutation.mutate(job.id)}
                              disabled={
                                buildResumeMutation.isPending &&
                                buildResumeMutation.variables === job.id
                              }
                              title="Rebuild resume"
                              aria-label="Rebuild resume"
                            >
                              <RotateCw
                                size={13}
                                className={
                                  buildResumeMutation.isPending &&
                                  buildResumeMutation.variables === job.id
                                    ? styles.spinning
                                    : undefined
                                }
                              />
                            </button>
                          </div>
                        </td>
                      )}
                    </Fragment>
                  );
                })}
                <td
                  className={styles.messagesCell}
                  style={{ width: MESSAGES_COLUMN_WIDTH }}
                >
                  <MessageButtons jobs={[job]} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div
        className={styles.stickyScrollbar}
        ref={bottomScrollRef}
        onScroll={(event) =>
          syncScroll(event.currentTarget, tableScrollRef.current)
        }
      >
        <div className={styles.scrollSpacer} style={{ width: tableWidth }} />
      </div>
    </div>
  );
}
