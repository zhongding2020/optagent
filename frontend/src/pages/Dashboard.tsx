import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../hooks/useApi'

export default function Dashboard() {
  const navigate = useNavigate()
  const [workflows, setWorkflows] = useState<{ name: string }[]>([])
  const [sessions, setSessions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.listWorkflows().then(setWorkflows).catch(() => {}),
      api.listSessions().then(setSessions).catch((e) => setError(e.message)),
    ]).finally(() => setLoading(false))
  }, [])

  const startSession = async (wf: string) => {
    const session = await api.createSession(wf)
    navigate(`/sessions/${session.id}`)
  }

  const statusBadge = (s: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-warning/10 text-warning',
      running: 'bg-accent/10 text-accent',
      completed: 'bg-success/10 text-success',
      error: 'bg-danger/10 text-danger',
      interrupted: 'bg-warning/10 text-warning',
    }
    return colors[s] || 'bg-bg-tertiary text-text-muted'
  }

  return (
    <div className="max-w-4xl mx-auto px-8 py-12">
      <div className="mb-10">
        <h1 className="text-2xl font-bold text-text-primary mb-1">OptAgent</h1>
        <p className="text-sm text-text-secondary">Agent-guided process parameter optimization</p>
      </div>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-lg bg-danger/10 border border-danger/30 text-xs text-danger">
          Connection error: {error}. <button onClick={() => window.location.reload()} className="underline">Retry</button>
        </div>
      )}

      {loading ? (
        <>
          <div className="h-4 w-24 bg-bg-tertiary rounded animate-pulse mb-4" />
          <div className="flex gap-3 mb-12">
            {[1,2,3].map(i => <div key={i} className="h-12 w-36 rounded-xl bg-bg-tertiary animate-pulse" />)}
          </div>
          <div className="h-4 w-28 bg-bg-tertiary rounded animate-pulse mb-4" />
          <div className="space-y-1">
            {[1,2].map(i => <div key={i} className="h-12 w-full rounded-xl bg-bg-tertiary animate-pulse" />)}
          </div>
        </>
      ) : (
      <>
      <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">Workflows</h2>
      <div className="flex gap-3 mb-12 flex-wrap">
        {workflows.map(wf => (
          <button key={wf.name} onClick={() => startSession(wf.name)}
            className="px-5 py-3 rounded-xl border border-border bg-bg-primary
                       hover:bg-bg-hover transition-colors text-sm font-medium text-text-primary
                       flex items-center gap-2 shadow-sm">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                 strokeLinecap="round" strokeLinejoin="round" className="text-accent shrink-0">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            {wf.name.replace('-', ' ')}
          </button>
        ))}
      </div>

      <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">Knowledge Base</h2>
      <button onClick={() => navigate('/kb')}
        className="w-full flex items-center gap-4 px-5 py-4 rounded-xl border border-border bg-bg-primary
                   hover:bg-bg-hover transition-colors mb-12 shadow-sm">
        <div className="w-10 h-10 rounded-lg bg-accent-light flex items-center justify-center shrink-0">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
               strokeLinecap="round" strokeLinejoin="round" className="text-accent">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            <line x1="8" y1="7" x2="16" y2="7" /><line x1="8" y1="11" x2="14" y2="11" />
            <line x1="8" y1="15" x2="12" y2="15" />
          </svg>
        </div>
        <div className="min-w-0">
          <div className="text-sm font-medium text-text-primary">Knowledge Base</div>
          <div className="text-xs text-text-muted">Upload and manage documents for context-aware search</div>
        </div>
        <svg className="ml-auto shrink-0 w-4 h-4 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>

      <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">Recent Sessions</h2>
      {sessions.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-sm text-text-muted">No sessions yet. Start a workflow above.</p>
        </div>
      ) : (
        <div className="space-y-1">
          {sessions.map((s: any) => (
            <button key={s.id} onClick={() => navigate(`/sessions/${s.id}`)}
              className="w-full text-left flex items-center justify-between px-4 py-3 rounded-xl
                         hover:bg-bg-hover transition-colors">
              <div className="flex items-center gap-3 min-w-0">
                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full shrink-0 ${statusBadge(s.status)}`}>
                  {s.status}
                </span>
                <span className="text-sm text-text-primary truncate">{s.id.slice(0, 8)}...</span>
              </div>
              <span className="text-xs text-text-muted shrink-0 ml-3">
                {new Date(s.created_at).toLocaleString()}
              </span>
            </button>
          ))}
        </div>
      )}
      </>
      )}
    </div>
  )
}
