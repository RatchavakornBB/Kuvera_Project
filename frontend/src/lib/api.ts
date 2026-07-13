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

export async function fetchDeals(): Promise<ApiDeal[]> {
  const res = await fetch(`${API_BASE_URL}/deals`);
  if (!res.ok) {
    throw new Error(`GET /deals failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchDeal(id: string): Promise<ApiDeal & Record<string, unknown>> {
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
