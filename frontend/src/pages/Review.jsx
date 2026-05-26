import { useState } from 'react';
import { useRecords, useSuspicious } from '../api.js';
import RecordTable from '../components/RecordTable.jsx';

const TABS = [
  { key: 'all', label: 'All Records' },
  { key: 'suspicious', label: 'Suspicious' },
];

export default function Review() {
  const [tab, setTab] = useState('all');
  const records = useRecords();
  const suspicious = useSuspicious();

  const activeQuery = tab === 'all' ? records : suspicious;

  return (
    <div className="animate-fade-in-up">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
          Analyst Review
        </h1>
        <p className="mt-1 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          Review normalised emission records. Approve, dispute, or lock rows for compliance audit.
        </p>
      </div>

      {/* Tab Bar */}
      <div className="flex items-center gap-6 mb-6 border-b" style={{ borderColor: 'var(--color-border)' }}>
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className="relative pb-3 text-sm font-medium transition-colors duration-200 cursor-pointer"
            style={{
              color: tab === t.key ? 'var(--color-accent)' : 'var(--color-text-secondary)',
            }}
          >
            {t.label}
            {t.key === 'suspicious' && suspicious.data?.length > 0 && (
              <span
                className="ml-2 px-2 py-0.5 rounded-full text-xs font-bold"
                style={{ background: 'rgba(239, 68, 68, 0.15)', color: 'var(--color-danger)' }}
              >
                {suspicious.data.length}
              </span>
            )}
            {tab === t.key && (
              <span
                className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full"
                style={{ background: 'var(--color-accent)' }}
              />
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeQuery.isLoading && (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-14 rounded-xl animate-shimmer" />
          ))}
        </div>
      )}

      {activeQuery.isError && (
        <div
          className="rounded-xl p-6 text-center text-sm border"
          style={{
            background: 'rgba(239, 68, 68, 0.06)',
            borderColor: 'rgba(239, 68, 68, 0.15)',
            color: 'var(--color-danger)',
          }}
        >
          <p className="font-medium">Failed to load records</p>
          <p className="mt-1 opacity-70">{activeQuery.error?.message || 'Network error'}</p>
          <button
            onClick={() => activeQuery.refetch()}
            className="mt-4 px-4 py-2 rounded-lg text-xs font-medium cursor-pointer transition-colors"
            style={{ background: 'var(--color-danger)', color: '#fff' }}
          >
            Retry
          </button>
        </div>
      )}

      {activeQuery.isSuccess && (
        <>
          {activeQuery.data.length === 0 ? (
            <div
              className="rounded-xl p-12 text-center border"
              style={{
                background: 'var(--color-surface-elevated)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-muted)',
              }}
            >
              <p className="text-4xl mb-3">∅</p>
              <p className="text-sm font-medium">
                {tab === 'suspicious' ? 'No suspicious records found' : 'No records yet'}
              </p>
              <p className="text-xs mt-1 opacity-60">Upload data from the Ingestion page to get started.</p>
            </div>
          ) : (
            <RecordTable records={activeQuery.data} showActions />
          )}
        </>
      )}
    </div>
  );
}
