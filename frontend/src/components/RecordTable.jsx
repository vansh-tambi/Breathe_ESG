import ActionButtons from './ActionButtons.jsx';

const STATUS_BADGE = {
  PENDING_REVIEW: { bg: 'rgba(245, 158, 11, 0.12)', color: '#f59e0b', label: 'Pending' },
  SUSPICIOUS: { bg: 'rgba(239, 68, 68, 0.12)', color: '#ef4444', label: 'Suspicious' },
  APPROVED: { bg: 'rgba(34, 197, 94, 0.12)', color: '#22c55e', label: 'Approved' },
  DISPUTED: { bg: 'rgba(168, 85, 247, 0.12)', color: '#a855f7', label: 'Disputed' },
  LOCKED: { bg: 'rgba(79, 140, 255, 0.12)', color: '#4f8cff', label: 'Locked' },
};

const SCOPE_LABEL = {
  SCOPE_1: { color: '#ef4444', short: 'S1' },
  SCOPE_2: { color: '#f59e0b', short: 'S2' },
  SCOPE_3: { color: '#4f8cff', short: 'S3' },
};

export default function RecordTable({ records, showActions = false }) {
  return (
    <div
      className="rounded-2xl border overflow-hidden"
      style={{ background: 'var(--color-surface-card)', borderColor: 'var(--color-border)' }}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm" style={{ borderCollapse: 'separate', borderSpacing: 0 }}>
          <thead>
            <tr style={{ background: 'var(--color-surface-elevated)' }}>
              {[
                'ID',
                'Scope',
                'Activity',
                'Date',
                'Qty',
                'Unit',
                'CO₂e (t)',
                'Status',
                ...(showActions ? ['Actions'] : []),
              ].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider"
                  style={{ color: 'var(--color-text-muted)', borderBottom: '1px solid var(--color-border)' }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {records.map((rec, idx) => {
              const badge = STATUS_BADGE[rec.review_status] || STATUS_BADGE.PENDING_REVIEW;
              const scope = SCOPE_LABEL[rec.scope_classification] || SCOPE_LABEL.SCOPE_1;

              return (
                <tr
                  key={rec.id}
                  className="transition-colors duration-150"
                  style={{
                    background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(79,140,255,0.04)')}
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background =
                      idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)')
                  }
                >
                  {/* Short UUID */}
                  <td
                    className="px-4 py-3"
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.72rem',
                      color: 'var(--color-text-secondary)',
                      borderBottom: '1px solid var(--color-border)',
                    }}
                  >
                    {rec.id?.slice(0, 8)}
                  </td>

                  {/* Scope Badge */}
                  <td className="px-4 py-3" style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <span
                      className="inline-block px-2 py-0.5 rounded text-xs font-bold"
                      style={{ background: `${scope.color}18`, color: scope.color }}
                    >
                      {scope.short}
                    </span>
                  </td>

                  {/* Activity */}
                  <td
                    className="px-4 py-3 text-xs"
                    style={{ color: 'var(--color-text-primary)', borderBottom: '1px solid var(--color-border)' }}
                  >
                    {rec.activity_type?.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())}
                  </td>

                  {/* Date */}
                  <td
                    className="px-4 py-3 text-xs"
                    style={{ color: 'var(--color-text-secondary)', borderBottom: '1px solid var(--color-border)' }}
                  >
                    {rec.reporting_date}
                  </td>

                  {/* Quantity */}
                  <td
                    className="px-4 py-3 text-xs text-right"
                    style={{
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--color-text-primary)',
                      borderBottom: '1px solid var(--color-border)',
                    }}
                  >
                    {Number(rec.normalized_quantity).toLocaleString('en', { maximumFractionDigits: 2 })}
                  </td>

                  {/* Unit */}
                  <td
                    className="px-4 py-3 text-xs"
                    style={{ color: 'var(--color-text-muted)', borderBottom: '1px solid var(--color-border)' }}
                  >
                    {rec.normalized_unit}
                  </td>

                  {/* CO2e */}
                  <td
                    className="px-4 py-3 text-xs text-right font-semibold"
                    style={{
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--color-text-primary)',
                      borderBottom: '1px solid var(--color-border)',
                    }}
                  >
                    {Number(rec.co2e_metric_tons).toLocaleString('en', { maximumFractionDigits: 4 })}
                  </td>

                  {/* Status */}
                  <td className="px-4 py-3" style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <span
                      className="inline-block px-2.5 py-1 rounded-lg text-xs font-semibold"
                      style={{ background: badge.bg, color: badge.color }}
                    >
                      {badge.label}
                    </span>
                  </td>

                  {/* Actions */}
                  {showActions && (
                    <td className="px-4 py-3" style={{ borderBottom: '1px solid var(--color-border)' }}>
                      <ActionButtons record={rec} />
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div
        className="flex items-center justify-between px-4 py-3 text-xs"
        style={{
          background: 'var(--color-surface-elevated)',
          color: 'var(--color-text-muted)',
          borderTop: '1px solid var(--color-border)',
        }}
      >
        <span>{records.length} record{records.length !== 1 ? 's' : ''}</span>
        <span>
          Total CO₂e:{' '}
          <strong style={{ color: 'var(--color-text-primary)' }}>
            {records
              .reduce((sum, r) => sum + Number(r.co2e_metric_tons || 0), 0)
              .toLocaleString('en', { maximumFractionDigits: 4 })}{' '}
            t
          </strong>
        </span>
      </div>
    </div>
  );
}
