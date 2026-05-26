import { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

export default function FileUploader({ uploadType, endpoint, accent }) {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [dataSourceId, setDataSourceId] = useState('');
  const inputRef = useRef(null);
  const qc = useQueryClient();

  const upload = useMutation({
    mutationFn: (formData) =>
      axios.post(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['records'] });
      setFile(null);
      setDataSourceId('');
    },
  });

  function handleSubmit(e) {
    e.preventDefault();
    if (!file || !dataSourceId.trim()) return;
    const fd = new FormData();
    fd.append('file', file);
    fd.append('data_source_id', dataSourceId.trim());
    upload.mutate(fd);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.name.endsWith('.csv')) {
      setFile(dropped);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Data Source ID */}
      <div>
        <label className="block text-xs font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
          Data Source ID
        </label>
        <input
          type="text"
          value={dataSourceId}
          onChange={(e) => setDataSourceId(e.target.value)}
          placeholder="e.g. 3fa85f64-5717-4562-b3fc-2c963f66afa6"
          className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all duration-200"
          style={{
            background: 'var(--color-surface-elevated)',
            border: '1px solid var(--color-border)',
            color: 'var(--color-text-primary)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8rem',
          }}
          onFocus={(e) => (e.target.style.borderColor = accent)}
          onBlur={(e) => (e.target.style.borderColor = 'var(--color-border)')}
        />
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className="relative rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all duration-300"
        style={{
          borderColor: dragOver ? accent : 'var(--color-border)',
          background: dragOver ? `${accent}08` : 'var(--color-surface-elevated)',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => setFile(e.target.files[0] || null)}
        />

        {file ? (
          <div>
            <p className="text-3xl mb-2">📄</p>
            <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
              {file.name}
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
              {(file.size / 1024).toFixed(1)} KB · Click to change
            </p>
          </div>
        ) : (
          <div>
            <p className="text-3xl mb-2">↑</p>
            <p className="text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>
              Drop a <span style={{ color: accent }}>.csv</span> file here or click to browse
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
              Accepted format: CSV with required headers for {uploadType.toUpperCase()} source
            </p>
          </div>
        )}
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={!file || !dataSourceId.trim() || upload.isPending}
        className="w-full py-3.5 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer"
        style={{
          background: !file || !dataSourceId.trim() ? 'var(--color-border)' : accent,
          color: !file || !dataSourceId.trim() ? 'var(--color-text-muted)' : '#fff',
          opacity: upload.isPending ? 0.7 : 1,
        }}
      >
        {upload.isPending ? 'Processing…' : 'Upload & Process'}
      </button>

      {/* Result Feedback */}
      {upload.isSuccess && (
        <div
          className="rounded-xl p-4 border animate-fade-in-up"
          style={{
            background: 'rgba(34, 197, 94, 0.06)',
            borderColor: 'rgba(34, 197, 94, 0.2)',
          }}
        >
          <p className="text-sm font-medium" style={{ color: 'var(--color-success)' }}>
            ✓ Upload processed successfully
          </p>
          <div className="mt-2 grid grid-cols-3 gap-4 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            <div>
              <span className="block font-bold text-lg" style={{ color: 'var(--color-success)' }}>
                {upload.data?.data?.processed_records_count ?? '—'}
              </span>
              Processed
            </div>
            <div>
              <span className="block font-bold text-lg" style={{ color: 'var(--color-danger)' }}>
                {upload.data?.data?.failed_records_count ?? '0'}
              </span>
              Failed
            </div>
            <div>
              <span className="block font-bold text-lg" style={{ color: 'var(--color-text-primary)' }}>
                {upload.data?.data?.status ?? '—'}
              </span>
              Status
            </div>
          </div>
        </div>
      )}

      {upload.isError && (
        <div
          className="rounded-xl p-4 border animate-fade-in-up"
          style={{
            background: 'rgba(239, 68, 68, 0.06)',
            borderColor: 'rgba(239, 68, 68, 0.2)',
          }}
        >
          <p className="text-sm font-medium" style={{ color: 'var(--color-danger)' }}>
            ✕ Upload failed
          </p>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
            {upload.error?.response?.data?.error || upload.error?.message || 'Unknown error'}
          </p>
        </div>
      )}
    </form>
  );
}
