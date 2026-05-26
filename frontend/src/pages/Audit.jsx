import { useAuditLog } from '../api.js';

const STATUS_STYLES = {
  APPROVE: { bg: 'rgba(34, 197, 94, 0.10)', color: '#22c55e', label: 'Approved' },
  DISPUTE: { bg: 'rgba(239, 68, 68, 0.10)', color: '#ef4444', label: 'Disputed' },
  FLAG_SUSPICIOUS: { bg: 'rgba(245, 158, 11, 0.10)', color: '#f59e0b', label: 'Flagged' },
  LOCK: { bg: 'rgba(79, 140, 255, 0.10)', color: '#4f8cff', label: 'Locked' },
};

export default function Audit() {
  const audit = useAuditLog();

  return (
    <div className="animate-fade-in-up">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
          Audit Trail
        </h1>
        <p className="mt-1 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          Immutable log of every review decision. This data cannot be modified or deleted.
        </p>
      </div>

      {/* Loading State */}
      {audit.isLoading && (
        <div className="space-y-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-16 rounded-xl animate-shimmer" />
          ))}
        </div>
      )}

      {/* Error State */}
      {audit.isError && (
        <div
          className="rounded-xl p-8 text-center border"
          style={{
            background: 'rgba(245, 158, 11, 0.06)',
            borderColor: 'rgba(245, 158, 11, 0.15)',
            color: 'var(--color-warning)',
          }}
        >
          <p className="text-4xl mb-3">⚠</p>
          <p className="text-sm font-medium">Audit endpoint not available yet</p>
          <p className="text-xs mt-2 opacity-60">
            The backend audit API will be connected once the review workflow is fully wired.
          </p>
        </div>
      )}

      {/* Data */}
      {audit.isSuccess && (
        <>
          {audit.data.length === 0 ? (
            <div
              className="rounded-xl p-12 text-center border"
              style={{
                background: 'var(--color-surface-elevated)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-muted)',
              }}
            >
              <p className="text-4xl mb-3">📋</p>
              <p className="text-sm font-medium">No audit events recorded yet</p>
              <p className="text-xs mt-1 opacity-60">
                Approve or reject records in the Review page to generate audit entries.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {audit.data.map((entry, idx) => {
                const style = STATUS_STYLES[entry.action_type] || STATUS_STYLES.APPROVE;
                return (
                  <div
                    key={entry.id || idx}
                    className="flex items-start gap-4 p-4 rounded-xl border transition-all duration-200 hover:translate-x-1"
                    style={{
                      background: 'var(--color-surface-card)',
                      borderColor: 'var(--color-border)',
                    }}
                  >
                    {/* Action Badge */}
                    <span
                      className="px-3 py-1 rounded-lg text-xs font-bold shrink-0 mt-0.5"
                      style={{ background: style.bg, color: style.color }}
                    >
                      {style.label}
                    </span>

                    {/* Details */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>
                        Record{' '}
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                          {entry.normalized_record?.slice(0, 8) || '—'}
                        </span>
                      </p>
                      {entry.notes && (
                        <p className="text-xs mt-1 truncate" style={{ color: 'var(--color-text-secondary)' }}>
                          {entry.notes}
                        </p>
                      )}
                    </div>

                    {/* Timestamp */}
                    <span className="text-xs shrink-0" style={{ color: 'var(--color-text-muted)' }}>
                      {entry.created_at
                        ? new Date(entry.created_at).toLocaleString('en-GB', {
                            day: '2-digit',
                            month: 'short',
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : '—'}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
