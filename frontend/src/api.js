import axios from 'axios';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// ── Axios Instance ──
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Hardcoded tenant for prototype — in production this comes from auth context
const DEFAULT_COMPANY_ID = '00000000-0000-0000-0000-000000000001';

// ── Ingestion Mutations ──

export function useUploadSAP() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (formData) =>
      api.post('/ingestion/sap-upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['records'] }),
  });
}

export function useUploadUtility() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (formData) =>
      api.post('/ingestion/utility-upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['records'] }),
  });
}

export function useUploadTravel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (formData) =>
      api.post('/ingestion/travel-upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['records'] }),
  });
}

// ── Review Queries ──

export function useRecords(companyId = DEFAULT_COMPANY_ID) {
  return useQuery({
    queryKey: ['records', companyId],
    queryFn: () =>
      api.get('/review/records/', { params: { company_id: companyId } }).then((r) => r.data),
  });
}

export function useSuspicious(companyId = DEFAULT_COMPANY_ID) {
  return useQuery({
    queryKey: ['suspicious', companyId],
    queryFn: () =>
      api.get('/review/suspicious/', { params: { company_id: companyId } }).then((r) => r.data),
  });
}

export function useAuditLog(companyId = DEFAULT_COMPANY_ID) {
  return useQuery({
    queryKey: ['audit', companyId],
    queryFn: () =>
      api.get('/review/audit/', { params: { company_id: companyId } }).then((r) => r.data),
    retry: false,
  });
}

// ── Review Actions ──

export function useApprove() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ recordId, notes, companyId = DEFAULT_COMPANY_ID }) =>
      api.post(`/review/approve/?company_id=${companyId}`, {
        record_id: recordId,
        notes,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['records'] });
      qc.invalidateQueries({ queryKey: ['suspicious'] });
      qc.invalidateQueries({ queryKey: ['audit'] });
    },
  });
}

export function useReject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ recordId, notes, companyId = DEFAULT_COMPANY_ID }) =>
      api.post(`/review/reject/?company_id=${companyId}`, {
        record_id: recordId,
        notes,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['records'] });
      qc.invalidateQueries({ queryKey: ['suspicious'] });
      qc.invalidateQueries({ queryKey: ['audit'] });
    },
  });
}

export function useLock() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ recordId, notes, companyId = DEFAULT_COMPANY_ID }) =>
      api.post(`/review/lock/?company_id=${companyId}`, {
        record_id: recordId,
        notes,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['records'] });
      qc.invalidateQueries({ queryKey: ['suspicious'] });
      qc.invalidateQueries({ queryKey: ['audit'] });
    },
  });
}
