import { useState } from 'react';
import FileUploader from '../components/FileUploader.jsx';

const UPLOAD_TYPES = [
  {
    key: 'sap',
    label: 'SAP Procurement',
    description: 'German-header fuel & material CSV exports from SAP',
    endpoint: '/api/ingestion/sap-upload/',
    accent: '#4f8cff',
  },
  {
    key: 'utility',
    label: 'Utility Portal',
    description: 'Electricity meter readings from utility billing portals',
    endpoint: '/api/ingestion/utility-upload/',
    accent: '#22c55e',
  },
  {
    key: 'travel',
    label: 'Travel (Concur)',
    description: 'Corporate travel exports — flights, hotels, ground transport',
    endpoint: '/api/ingestion/travel-upload/',
    accent: '#f59e0b',
  },
];

export default function Upload() {
  const [activeType, setActiveType] = useState('sap');
  const active = UPLOAD_TYPES.find((t) => t.key === activeType);

  return (
    <div className="animate-fade-in-up">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
          Data Ingestion
        </h1>
        <p className="mt-1 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          Upload CSV exports from your configured data sources. Each file is validated, stored raw, and normalised automatically.
        </p>
      </div>

      {/* Source Type Tabs */}
      <div
        className="flex gap-2 p-1 rounded-xl mb-8"
        style={{ background: 'var(--color-surface-elevated)' }}
      >
        {UPLOAD_TYPES.map((type) => (
          <button
            key={type.key}
            onClick={() => setActiveType(type.key)}
            className="flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer"
            style={{
              background: activeType === type.key ? 'var(--color-surface-card)' : 'transparent',
              color: activeType === type.key ? type.accent : 'var(--color-text-secondary)',
              boxShadow:
                activeType === type.key
                  ? `0 0 0 1px ${type.accent}33, 0 2px 8px rgba(0,0,0,0.2)`
                  : 'none',
            }}
          >
            {type.label}
          </button>
        ))}
      </div>

      {/* Active Upload Card */}
      <div
        className="rounded-2xl p-8 border transition-all duration-300"
        style={{
          background: 'var(--color-surface-card)',
          borderColor: `${active.accent}22`,
        }}
      >
        <div className="mb-6">
          <h2 className="text-lg font-semibold" style={{ color: active.accent }}>
            {active.label}
          </h2>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
            {active.description}
          </p>
        </div>

        <FileUploader uploadType={active.key} endpoint={active.endpoint} accent={active.accent} />
      </div>
    </div>
  );
}
