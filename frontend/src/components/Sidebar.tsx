import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../hooks/useApi'
import ThemeToggle from './ThemeToggle'

interface Session {
  id: string
  workflow_name: string
  name?: string
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
  const [editingId, setEditingId] = useState<string | null>(null)

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

  const saveRename = async (id: string, name: string) => {
    try {
      const trimmed = name.trim()
      if (!trimmed) { setEditingId(null); return }
      await api.renameSession(id, trimmed)
      setSessions(prev => prev.map(s => s.id === id ? { ...s, name: trimmed } : s))
    } catch (e) { console.error(e) }
    setEditingId(null)
  }

  const handleDelete = async (id: string) => {
    try {
      await api.deleteSession(id)
      setSessions(prev => prev.filter(s => s.id !== id))
      if (id === activeId) navigate('/')
    } catch (e) { console.error(e) }
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
          <div key={s.id} className="group relative">
            <button
              onClick={() => { setEditingId(null); navigate(`/sessions/${s.id}`) }}
              className={`w-full text-left px-3 py-2 mb-0.5 rounded-lg text-sm transition-colors
                ${s.id === activeId
                  ? 'bg-bg-active text-text-primary'
                  : 'text-text-secondary hover:bg-bg-hover'
                }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-xs w-4 text-center flex-shrink-0">{statusIcon[s.status] || '○'}</span>
                {editingId === s.id ? (
                  <input
                    autoFocus
                    defaultValue={s.name || s.workflow_name}
                    className="flex-1 text-xs px-1 py-0.5 rounded border border-accent bg-bg-primary outline-none"
                    onClick={e => e.stopPropagation()}
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        e.stopPropagation()
                        saveRename(s.id, (e.target as HTMLInputElement).value)
                      }
                      if (e.key === 'Escape') { setEditingId(null); e.stopPropagation() }
                    }}
                    onBlur={() => setEditingId(null)}
                  />
                ) : (
                  <>
                    <span className="truncate flex-1 text-xs font-medium">{s.name || s.workflow_name}</span>
                    <span className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity" onClick={e => e.stopPropagation()}>
                      <button onClick={() => setEditingId(s.id)}
                        className="p-0.5 text-text-muted hover:text-text-primary rounded"
                        title="Rename">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      </button>
                      <button onClick={() => { if (confirm('Delete this session?')) handleDelete(s.id) }}
                        className="p-0.5 text-text-muted hover:text-danger rounded"
                        title="Delete">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                      </button>
                    </span>
                  </>
                )}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[10px] text-text-muted">{s.status}</span>
                <span className="text-[10px] text-text-muted">{new Date(s.created_at).toLocaleDateString()}</span>
              </div>
            </button>
          </div>
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
