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

export interface ApiDocumentWithDeal extends ApiDocument {
  deal: { id: string; name: string } | null;
}

export async function fetchDocuments(params: {
  deal_id?: string;
  type?: string;
  status?: string;
  q?: string;
}): Promise<ApiDocumentWithDeal[]> {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) search.set(key, value);
  }
  const res = await fetch(`${API_BASE_URL}/documents?${search.toString()}`);
  if (!res.ok) {
    throw new Error(`GET /documents failed: ${res.status}`);
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

export interface ApiKeyDateNotification {
  document_id: string;
  document_name: string;
  deal_id: string;
  deal_name: string | null;
  key_date: string;
  days_until: number;
}

export async function fetchKeyDateNotifications(days = 30): Promise<ApiKeyDateNotification[]> {
  const res = await fetch(`${API_BASE_URL}/notifications/key-dates?days=${days}`);
  if (!res.ok) {
    throw new Error(`GET /notifications/key-dates failed: ${res.status}`);
  }
  return res.json();
}

export interface ApiAgentConfig {
  id: string;
  agent_name: string;
  model_id: string;
  skill_content: string;
  updated_at: string;
}

export interface ApiPendingChange {
  id: string;
  agent_name: string;
  change_type: 'model_id' | 'skill_content';
  old_value: string | null;
  new_value: string;
  status: 'pending' | 'approved' | 'rejected';
  proposed_at: string;
  reviewed_at: string | null;
}

export interface ApiAuditEntry {
  id: string;
  agent_name: string;
  change_type: string;
  old_value: string | null;
  new_value: string;
  action: 'approved' | 'rejected';
  created_at: string;
}

export async function fetchAgentConfigs(): Promise<ApiAgentConfig[]> {
  const res = await fetch(`${API_BASE_URL}/admin/agents`);
  if (!res.ok) throw new Error(`GET /admin/agents failed: ${res.status}`);
  return res.json();
}

export async function proposeAgentChange(
  agentName: string,
  changeType: 'model_id' | 'skill_content',
  newValue: string,
): Promise<ApiPendingChange> {
  const res = await fetch(`${API_BASE_URL}/admin/agents/${agentName}/propose`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ change_type: changeType, new_value: newValue }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(`POST /admin/agents/${agentName}/propose failed: ${res.status} ${body ? JSON.stringify(body.detail) : ''}`);
  }
  return res.json();
}

export async function fetchPendingApprovals(): Promise<ApiPendingChange[]> {
  const res = await fetch(`${API_BASE_URL}/admin/pending-approvals`);
  if (!res.ok) throw new Error(`GET /admin/pending-approvals failed: ${res.status}`);
  return res.json();
}

export async function resolvePendingChange(
  changeId: string,
  action: 'approve' | 'reject',
): Promise<ApiPendingChange> {
  const res = await fetch(`${API_BASE_URL}/admin/pending-approvals/${changeId}/${action}`, { method: 'POST' });
  if (!res.ok) throw new Error(`POST /admin/pending-approvals/${changeId}/${action} failed: ${res.status}`);
  return res.json();
}

export async function fetchAuditLog(): Promise<ApiAuditEntry[]> {
  const res = await fetch(`${API_BASE_URL}/admin/audit-log`);
  if (!res.ok) throw new Error(`GET /admin/audit-log failed: ${res.status}`);
  return res.json();
}

export interface ApiContradiction {
  id: string;
  deal_id: string;
  description: string;
  source_excerpt: string | null;
  status: 'unconfirmed' | 'corroborated' | 'resolved' | 'refuted';
  corroboration_count: number;
  first_flagged_at: string;
  last_seen_at: string;
  resolved_at: string | null;
  resolution_note: string | null;
  promoted_to_knowledge_base: boolean;
}

export async function fetchContradictions(dealId: string): Promise<ApiContradiction[]> {
  const res = await fetch(`${API_BASE_URL}/deals/${dealId}/contradictions`);
  if (!res.ok) throw new Error(`GET /deals/${dealId}/contradictions failed: ${res.status}`);
  return res.json();
}

export async function resolveContradiction(
  dealId: string,
  contradictionId: string,
  resolution: 'resolved' | 'refuted',
  note: string,
): Promise<ApiContradiction> {
  const res = await fetch(`${API_BASE_URL}/deals/${dealId}/contradictions/${contradictionId}/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resolution, note }),
  });
  if (!res.ok) throw new Error(`POST resolve contradiction failed: ${res.status}`);
  return res.json();
}

export interface ApiKnowledgeRecord {
  id: string;
  source_deal_id: string | null;
  category: string;
  company_name: string | null;
  industry: string | null;
  content: Record<string, unknown>;
  summary: string;
  created_at?: string;
  similarity?: number;
}

export async function fetchKnowledgeRecords(params: {
  industry?: string;
  category?: string;
}): Promise<ApiKnowledgeRecord[]> {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) search.set(key, value);
  }
  const res = await fetch(`${API_BASE_URL}/admin/knowledge-base?${search.toString()}`);
  if (!res.ok) throw new Error(`GET /admin/knowledge-base failed: ${res.status}`);
  return res.json();
}

export async function searchKnowledgeRecords(q: string, industry?: string): Promise<ApiKnowledgeRecord[]> {
  const search = new URLSearchParams({ q });
  if (industry) search.set('industry', industry);
  const res = await fetch(`${API_BASE_URL}/admin/knowledge-base/search?${search.toString()}`);
  if (!res.ok) throw new Error(`GET /admin/knowledge-base/search failed: ${res.status}`);
  return res.json();
}

export async function refreshIndustryBrief(industry: string): Promise<ApiKnowledgeRecord> {
  const res = await fetch(`${API_BASE_URL}/admin/knowledge-base/refresh-industry-brief`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ industry }),
  });
  if (!res.ok) throw new Error(`POST refresh-industry-brief failed: ${res.status}`);
  return res.json();
}

export async function refreshCompetitorBrief(companyName: string, industry: string): Promise<ApiKnowledgeRecord> {
  const res = await fetch(`${API_BASE_URL}/admin/knowledge-base/refresh-competitor-brief`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ company_name: companyName, industry }),
  });
  if (!res.ok) throw new Error(`POST refresh-competitor-brief failed: ${res.status}`);
  return res.json();
}

export async function closeDeal(dealId: string, outcome: 'won' | 'lost'): Promise<{ knowledge_records_created: number }> {
  const res = await fetch(`${API_BASE_URL}/deals/${dealId}/close`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ outcome }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(`POST /deals/${dealId}/close failed: ${res.status} ${body ? JSON.stringify(body.detail) : ''}`);
  }
  return res.json();
}

export interface ApiAgentActivity {
  thread_id: string;
  deal_id: string;
  document_id: string | null;
  node: string;
  status: 'success' | 'failed';
  ts: string;
  step: number | null;
  deal_name: string | null;
  document_name: string | null;
}

export async function fetchAgentActivity(limit = 50): Promise<ApiAgentActivity[]> {
  const res = await fetch(`${API_BASE_URL}/agent-hub/activity?limit=${limit}`);
  if (!res.ok) {
    throw new Error(`GET /agent-hub/activity failed: ${res.status}`);
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
