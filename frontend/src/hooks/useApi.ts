const BASE = 'http://localhost:8020/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export const api = {
  listWorkflows: () => request<{ name: string }[]>('/workflows'),
  createSession: (workflowName: string) =>
    request<{ id: string }>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ workflow_name: workflowName }),
    }),
  listSessions: () => request<Record<string, unknown>[]>('/sessions'),
  getSession: (id: string) => request<Record<string, unknown>>(`/sessions/${id}`),
  terminateSession: (id: string) =>
    request<{ ok: boolean }>(`/sessions/${id}/terminate`, { method: 'POST' }),
  listSkills: () => request<Record<string, unknown>[]>('/skills'),
  listKbDocuments: () => request<Record<string, unknown>[]>('/kb/documents'),
  listKbFiles: () => request<Record<string, unknown>[]>('/kb/files'),
  getKbStats: () => request<Record<string, unknown>>('/kb/stats'),
  uploadKbDocument: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE}/kb/upload`, { method: 'POST', body: form })
    return res.json()
  },
  deleteKbDocument: (id: string) =>
    request<{ ok: boolean }>(`/kb/documents/${id}`, { method: 'DELETE' }),
  searchKb: (q: string) => request<Record<string, unknown>[]>(`/kb/search?q=${encodeURIComponent(q)}&top_k=5`),
  getAnalysisData: (sessionId: string) =>
    request<Record<string, unknown>>(`/sessions/${sessionId}/data`),
}
