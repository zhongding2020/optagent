import { useEffect, useState } from 'react'
import { api } from '../hooks/useApi'
import KbDocumentList from '../components/KbDocumentList'
import KbUploadProgress from '../components/KbUploadProgress'

export default function KnowledgeBase() {
  const [docs, setDocs] = useState<any[]>([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState<{ phase: string; progress: number } | null>(null)

  const loadDocs = () => { api.listKbDocuments().then(setDocs).catch(() => {}) }
  useEffect(loadDocs, [])

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

  return (
    <div className="max-w-3xl mx-auto px-8 py-12">
      <h1 className="text-xl font-bold text-text-primary mb-1">Knowledge Base</h1>
      <p className="text-sm text-text-secondary mb-8">Upload PDF, Markdown, or text files</p>

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

      <KbDocumentList documents={docs} onDelete={(id) => {
        api.deleteKbDocument(id).then(loadDocs).catch(() => {})
      }} />
    </div>
  )
}
