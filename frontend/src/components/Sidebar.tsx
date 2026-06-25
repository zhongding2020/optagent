import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../hooks/useApi'
import ThemeToggle from './ThemeToggle'

interface Session {
  id: string
  workflow_name: string
  status: string
  created_at: string
}

const statusIcon: Record<string, string> = {
  pending: '○',
  running: '▶',
  completed: '✓',
  error: '✕',
  interrupted: '■',
}

export default function Sidebar() {
  const navigate = useNavigate()
  const { id: activeId } = useParams<{ id: string }>()
  const [sessions, setSessions] = useState<Session[]>([])
  const [filter, setFilter] = useState('')

  useEffect(() => {
    api.listSessions().then((s: any) => setSessions(s)).catch(() => {})
  }, [])

  const filtered = sessions.filter(s =>
    s.id.toLowerCase().includes(filter.toLowerCase()) ||
    s.status.toLowerCase().includes(filter.toLowerCase())
  )

  const newSession = async () => {
    try {
      const session = await api.createSession('process-optimization')
      navigate(`/sessions/${session.id}`)
    } catch {}
  }

  return (
    <div className="w-[var(--color-sidebar-width)] h-screen flex flex-col border-r border-border bg-bg-sidebar flex-shrink-0">
      {/* Header */}
      <div className="px-3 pt-3 pb-2">
        <button
          onClick={newSession}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-border
                     text-sm font-medium text-text-primary hover:bg-bg-hover transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Search */}
      <div className="px-3 pb-2">
        <input
          type="text"
          placeholder="Search sessions..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="w-full px-3 py-1.5 text-xs rounded-md border border-border bg-bg-primary
                     text-text-primary placeholder:text-text-muted outline-none
                     focus:border-accent transition-colors"
        />
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto px-2">
        {filtered.length === 0 && (
          <div className="px-3 py-4 text-xs text-text-muted text-center">
            {sessions.length === 0 ? 'No sessions yet' : 'No matches'}
          </div>
        )}
        {filtered.map(s => (
          <button
            key={s.id}
            onClick={() => navigate(`/sessions/${s.id}`)}
            className={`w-full text-left px-3 py-2 mb-0.5 rounded-lg text-sm transition-colors
              ${s.id === activeId
                ? 'bg-bg-active text-text-primary'
                : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
              }`}
          >
            <div className="flex items-center gap-2">
              <span className="text-xs w-4 text-center flex-shrink-0">{statusIcon[s.status] || '○'}</span>
              <span className="truncate flex-1 text-xs font-medium">
                {s.workflow_name}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] text-text-muted">{s.status}</span>
              <span className="text-[10px] text-text-muted">
                {new Date(s.created_at).toLocaleDateString()}
              </span>
            </div>
          </button>
        ))}
      </div>

      {/* Footer */}
      <div className="px-3 py-2 border-t border-border flex items-center justify-between">
        <a href="/" className="text-xs text-text-muted hover:text-text-secondary transition-colors">Dashboard</a>
        <a href="/kb" className="text-xs text-text-muted hover:text-text-secondary transition-colors">KB</a>
        <ThemeToggle />
      </div>
    </div>
  )
}
