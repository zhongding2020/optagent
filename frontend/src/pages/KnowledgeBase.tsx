import { useEffect, useRef, useState } from 'react'
import { api } from '../hooks/useApi'
import KbDocumentList from '../components/KbDocumentList'
import KbUploadProgress from '../components/KbUploadProgress'

type Tab = 'upload' | 'documents' | 'search' | 'stats'

export default function KnowledgeBase() {
  const [tab, setTab] = useState<Tab>('upload')

  // Upload state
  const [docs, setDocs] = useState<any[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState<{ phase: string; progress: number } | null>(null)

  // Files state
  const [files, setFiles] = useState<any[]>([])
  const [expandedFile, setExpandedFile] = useState<string | null>(null)

  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Stats state
  const [stats, setStats] = useState<any>(null)

  const loadFiles = () => { api.listKbFiles().then((f: any) => setFiles(f)).catch(() => {}) }
  const loadStats = () => { api.getKbStats().then((s: any) => setStats(s)).catch(() => {}) }
  const loadDocs = () => { api.listKbDocuments().then(setDocs).catch(() => {}) }
  useEffect(loadDocs, [])
  useEffect(() => { if (tab === 'documents') loadFiles() }, [tab])
  useEffect(() => { if (tab === 'stats') loadStats() }, [tab])

  const handleUpload = async (file: File) => {
    setUploading(true)
    try {
      const result: any = await api.uploadKbDocument(file)
      const poll = setInterval(async () => {
        const job = await fetch('http://localhost:8020/api/kb/jobs/' + result.job_id).then(r => r.json())
        if (job.phase === 'done' || job.phase === 'error') {
          clearInterval(poll); setUploading(false); setProgress(null); loadDocs()
        } else {
          setProgress({ phase: job.phase, progress: job.progress })
        }
      }, 1000)
    } catch (e) { setUploading(false); console.error(e) }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearching(true)
    try {
      const results = await api.searchKb(searchQuery.trim())
      setSearchResults(results)
    } catch { setSearchResults([]) }
    setSearching(false)
  }

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: 'upload', label: 'Upload', icon: '↑' },
    { key: 'documents', label: 'Documents', icon: '📄' },
    { key: 'search', label: 'Search', icon: '🔍' },
    { key: 'stats', label: 'Stats', icon: '📊' },
  ]

  return (
    <div className="max-w-3xl mx-auto px-8 py-12">
      <h1 className="text-xl font-bold text-text-primary mb-1">Knowledge Base Management</h1>
      <p className="text-sm text-text-secondary mb-6">Upload documents, explore chunks, and monitor search performance</p>

      {/* Tabs */}
      <div className="flex gap-1 mb-8 border-b border-border">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all -mb-px
              ${tab === t.key
                ? 'border-accent text-accent'
                : 'border-transparent text-text-muted hover:text-text-secondary hover:border-border'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Upload Tab */}
      {tab === 'upload' && (
        <div>
          <div className="p-6 rounded-xl border border-dashed border-border bg-bg-secondary mb-8 text-center">
            <label className="cursor-pointer block">
              <input type="file" accept=".pdf,.md,.txt" className="hidden"
                onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])} disabled={uploading} />
              <div className="text-sm text-text-muted">
                {uploading ? 'Uploading...' : 'Click to upload PDF, Markdown, or TXT file'}
              </div>
            </label>
            {progress && <KbUploadProgress phase={progress.phase} progress={progress.progress} />}
          </div>

          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-3">Indexed Documents</h3>
          <KbDocumentList documents={docs} onDelete={(id) => {
            api.deleteKbDocument(id).then(() => { loadDocs(); loadFiles() }).catch(() => {})
          }} />
        </div>
      )}

      {/* Documents Tab */}
      {tab === 'documents' && (
        <div>
          {files.length === 0 ? (
            <p className="text-sm text-text-muted italic">No documents indexed</p>
          ) : (
            <div className="space-y-4">
              {files.map((f: any) => (
                <div key={f.source}
                  className="rounded-xl border border-border bg-bg-primary overflow-hidden">
                  <button onClick={() => setExpandedFile(expandedFile === f.source ? null : f.source)}
                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-bg-secondary transition-colors">
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-text-primary truncate">{f.source.replace(/^.*\//, '')}</div>
                      <div className="text-xs text-text-muted">{f.chunk_count} chunks</div>
                    </div>
                    <svg className={`w-4 h-4 text-text-muted transition-transform ${expandedFile === f.source ? 'rotate-180' : ''}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </button>
                  {expandedFile === f.source && (
                    <div className="border-t border-border divide-y divide-border">
                      {f.chunks.map((chunk: any) => (
                        <div key={chunk.id} className="px-4 py-3 bg-bg-secondary">
                          <div className="text-xs text-text-muted mb-1">ID: {chunk.id}</div>
                          <div className="text-xs text-text-primary leading-relaxed font-mono bg-bg-primary p-2 rounded-lg max-h-32 overflow-y-auto">
                            {chunk.metadata?.text || '(chunk content not stored in result)'}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Search Tab */}
      {tab === 'search' && (
        <div>
          <div className="flex gap-2 mb-6">
            <input ref={searchInputRef} type="text"
              value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleSearch() }}
              placeholder="Search knowledge base..."
              className="flex-1 px-4 py-2.5 rounded-xl border border-border bg-bg-secondary
                         text-sm text-text-primary placeholder:text-text-muted outline-none
                         focus:border-accent focus:ring-1 focus:ring-accent/30 transition-all" />
            <button onClick={handleSearch} disabled={searching || !searchQuery.trim()}
              className="px-4 py-2.5 rounded-xl bg-accent text-white text-sm font-medium
                         hover:bg-accent-hover disabled:opacity-40 transition-all">
              {searching ? 'Searching...' : 'Search'}
            </button>
          </div>

          {searchResults.length > 0 && (
            <div className="space-y-3">
              <div className="text-xs text-text-muted">{searchResults.length} result(s)</div>
              {searchResults.map((r: any, i) => (
                <div key={i} className="p-4 rounded-xl border border-border bg-bg-primary">
                  <div className="text-xs text-text-muted mb-1">{r.metadata?.source || '?'}</div>
                  <div className="text-xs text-text-primary leading-relaxed">{r.content}</div>
                </div>
              ))}
            </div>
          )}
          {searchResults.length === 0 && !searching && searchQuery && (
            <p className="text-sm text-text-muted italic">No results found</p>
          )}
        </div>
      )}

      {/* Stats Tab */}
      {tab === 'stats' && stats && (
        <div>
          {/* Overview cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { label: 'Documents', value: stats.total_files, color: 'text-accent' },
              { label: 'Chunks', value: stats.total_chunks, color: 'text-accent' },
              { label: 'Total Queries', value: stats.total_queries, color: 'text-text-primary' },
              { label: 'Hit Rate', value: `${stats.hit_rate}%`, color: stats.hit_rate > 50 ? 'text-success' : 'text-warning' },
            ].map(card => (
              <div key={card.label} className="p-4 rounded-xl border border-border bg-bg-primary text-center">
                <div className={`text-2xl font-bold ${card.color}`}>{card.value}</div>
                <div className="text-xs text-text-muted mt-1">{card.label}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="p-4 rounded-xl border border-border bg-bg-primary">
              <div className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">Queries with results</div>
              <div className="text-lg font-bold text-success">{stats.queries_with_results}</div>
            </div>
            <div className="p-4 rounded-xl border border-border bg-bg-primary">
              <div className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1">Queries no results</div>
              <div className="text-lg font-bold text-warning">{stats.queries_no_results}</div>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Embedding Model</h3>
            <div className="p-3 rounded-xl border border-border bg-bg-primary">
              <div className="text-sm text-text-primary">{stats.embedding_model}</div>
            </div>
          </div>

          {/* Top sources */}
          {stats.top_sources && stats.top_sources.length > 0 && (
            <div className="mb-6">
              <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Top Sources by Hits</h3>
              <div className="rounded-xl border border-border overflow-hidden bg-bg-primary">
                {stats.top_sources.map((s: any, i: number) => (
                  <div key={i} className="flex items-center justify-between px-4 py-2.5 border-b border-border last:border-b-0">
                    <span className="text-sm text-text-primary truncate">{s.source.replace(/^.*\//, '')}</span>
                    <span className="text-sm font-medium text-accent">{s.hits}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent queries */}
          {stats.recent_queries && stats.recent_queries.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Recent Queries</h3>
              <div className="rounded-xl border border-border overflow-hidden bg-bg-primary">
                {stats.recent_queries.map((q: any, i: number) => (
                  <div key={i} className="flex items-center justify-between px-4 py-2.5 border-b border-border last:border-b-0">
                    <div className="min-w-0 flex-1">
                      <div className="text-sm text-text-primary truncate">{q.query}</div>
                      <div className="text-xs text-text-muted">{q.time?.replace('T', ' ').slice(0, 19)}</div>
                    </div>
                    <span className={`text-xs font-medium ml-3 ${q.results > 0 ? 'text-success' : 'text-text-muted'}`}>
                      {q.results} hit{q.results !== 1 ? 's' : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
