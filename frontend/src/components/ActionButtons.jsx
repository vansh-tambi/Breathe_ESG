import { useApprove, useReject, useLock } from '../api.js';

export default function ActionButtons({ record }) {
  const approve = useApprove();
  const reject = useReject();
  const lock = useLock();

  const isLocked = record.is_locked;
  const isApproved = record.review_status === 'APPROVED';
  const isAlreadyLocked = record.review_status === 'LOCKED';

  const btnBase =
    'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed';

  return (
    <div className="flex items-center gap-2">
      {/* Approve */}
      <button
        disabled={isLocked || isApproved || isAlreadyLocked || approve.isPending}
        onClick={() => approve.mutate({ recordId: record.id, notes: '' })}
        className={btnBase}
        style={{
          background: 'rgba(34, 197, 94, 0.12)',
          color: '#22c55e',
          border: '1px solid rgba(34, 197, 94, 0.2)',
        }}
        onMouseEnter={(e) => {
          if (!e.currentTarget.disabled) {
            e.currentTarget.style.background = 'rgba(34, 197, 94, 0.25)';
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(34, 197, 94, 0.12)';
        }}
        title={isLocked ? 'Record is locked' : isApproved ? 'Already approved' : 'Approve this record'}
      >
        {approve.isPending ? '…' : '✓'}
      </button>

      {/* Reject / Dispute */}
      <button
        disabled={isLocked || isAlreadyLocked || reject.isPending}
        onClick={() => reject.mutate({ recordId: record.id, notes: '' })}
        className={btnBase}
        style={{
          background: 'rgba(239, 68, 68, 0.12)',
          color: '#ef4444',
          border: '1px solid rgba(239, 68, 68, 0.2)',
        }}
        onMouseEnter={(e) => {
          if (!e.currentTarget.disabled) {
            e.currentTarget.style.background = 'rgba(239, 68, 68, 0.25)';
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(239, 68, 68, 0.12)';
        }}
        title={isLocked ? 'Record is locked' : 'Dispute this record'}
      >
        {reject.isPending ? '…' : '✕'}
      </button>

      {/* Lock */}
      <button
        disabled={isLocked || isAlreadyLocked || lock.isPending}
        onClick={() => lock.mutate({ recordId: record.id, notes: '' })}
        className={btnBase}
        style={{
          background: 'rgba(79, 140, 255, 0.12)',
          color: '#4f8cff',
          border: '1px solid rgba(79, 140, 255, 0.2)',
        }}
        onMouseEnter={(e) => {
          if (!e.currentTarget.disabled) {
            e.currentTarget.style.background = 'rgba(79, 140, 255, 0.25)';
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'rgba(79, 140, 255, 0.12)';
        }}
        title={isLocked ? 'Already locked' : 'Lock for compliance audit'}
      >
        {lock.isPending ? '…' : '🔒'}
      </button>
    </div>
  );
}
