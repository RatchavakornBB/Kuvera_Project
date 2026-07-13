const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export interface ApiDeal {
  id: string;
  name: string;
  client: string;
  industries: string[];
  stage: string;
  stage_entered_at: string;
  status: 'On track' | 'Needs attention' | 'Stalled' | 'Closed';
  owner: { id: string; full_name: string; initials: string } | null;
  docs_pending: number;
  risk_flags: number;
  updated_at: string;
}

export interface ApiContact {
  id: string;
  name: string;
  role: string | null;
  company: string | null;
  last_contacted_at: string | null;
}

export interface ApiDocument {
  id: string;
  deal_id: string;
  name: string;
  type: string;
  storage_path: string | null;
  status: 'requested' | 'received' | 'pending' | 'under_review' | 'approved' | 'rejected';
  summary: string | null;
  key_date: string | null;
  uploaded_at: string;
  clauses: { label: string; text: string }[];
}

export interface ApiTask {
  id: string;
  text: string;
  owner_id: string | null;
  due_date: string | null;
  done: boolean;
}

export interface ApiMeetingNote {
  id: string;
  occurred_at: string;
  attendees: string[];
  summary: string | null;
}

export interface ApiDDItem {
  id: string;
  item: string;
  status: 'pending' | 'received' | 'reviewed';
}

export interface ApiMilestone {
  id: string;
  label: string;
  occurred_at: string | null;
  sort_order: number;
}

export interface ApiDealDetail extends ApiDeal {
  contacts: ApiContact[];
  documents: ApiDocument[];
  tasks: ApiTask[];
  meeting_notes: ApiMeetingNote[];
  dd_items: ApiDDItem[];
  milestones: ApiMilestone[];
}

export async function fetchDeals(): Promise<ApiDeal[]> {
  const res = await fetch(`${API_BASE_URL}/deals`);
  if (!res.ok) {
    throw new Error(`GET /deals failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchDeal(id: string): Promise<ApiDealDetail> {
  const res = await fetch(`${API_BASE_URL}/deals/${id}`);
  if (!res.ok) {
    throw new Error(`GET /deals/${id} failed: ${res.status}`);
  }
  return res.json();
}

export async function createDeal(body: { name: string; client: string; industries: string[] }): Promise<ApiDeal> {
  const res = await fetch(`${API_BASE_URL}/deals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`POST /deals failed: ${res.status}`);
  }
  return res.json();
}

export async function uploadDocument(dealId: string, file: File): Promise<ApiDocument> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE_URL}/deals/${dealId}/documents`, { method: 'POST', body: formData });
  if (!res.ok) {
    throw new Error(`POST /deals/${dealId}/documents failed: ${res.status}`);
  }
  return res.json();
}

export interface AnalyzeResult {
  summary: string;
  risk_flags: { severity: string; description: string; source_excerpt: string }[];
  ic_memo_draft: string | null;
  pricing_note: string | null;
  pricing_error: { node: string; attempts: number; reason: string; raw_error: string } | null;
}

export async function analyzeDocument(dealId: string, documentId: string): Promise<AnalyzeResult> {
  const res = await fetch(`${API_BASE_URL}/deals/${dealId}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ document_id: documentId }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(`POST /deals/${dealId}/analyze failed: ${res.status} ${body ? JSON.stringify(body.detail) : ''}`);
  }
  return res.json();
}

export interface ApiAnalysis extends AnalyzeResult {
  document_id: string;
  created_at: string;
}

export async function fetchLatestAnalysis(dealId: string): Promise<ApiAnalysis | null> {
  const res = await fetch(`${API_BASE_URL}/deals/${dealId}/analysis`);
  if (!res.ok) {
    throw new Error(`GET /deals/${dealId}/analysis failed: ${res.status}`);
  }
  return res.json();
}

export async function createTask(
  dealId: string,
  body: { text: string; owner_id?: string | null; due_date?: string | null },
): Promise<ApiTask> {
  const res = await fetch(`${API_BASE_URL}/deals/${dealId}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`POST /deals/${dealId}/tasks failed: ${res.status}`);
  }
  return res.json();
}

export async function updateTask(
  dealId: string,
  taskId: string,
  body: { done?: boolean; text?: string; due_date?: string | null },
): Promise<ApiTask> {
  const res = await fetch(`${API_BASE_URL}/deals/${dealId}/tasks/${taskId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`PATCH /deals/${dealId}/tasks/${taskId} failed: ${res.status}`);
  }
  return res.json();
}
