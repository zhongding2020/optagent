 import { useEffect, useState } from 'react'
 import { api } from '../hooks/useApi'
 import KbDocumentList from '../components/KbDocumentList'
 import KbUploadProgress from '../components/KbUploadProgress'
 
 export default function KnowledgeBase() {
   const [docs, setDocs] = useState<Record<string, unknown>[]>([])
   const [uploading, setUploading] = useState(false)
   const [progress, setProgress] = useState<{ phase: string; progress: number } | null>(null)
 
   const loadDocs = () => { api.listKbDocuments().then(setDocs).catch(console.error) }
   useEffect(loadDocs, [])
 
   const handleUpload = async (file: File) => {
     setUploading(true)
     try {
       const result: any = await api.uploadKbDocument(file)
       const poll = setInterval(async () => {
         const job = await fetch(`http://localhost:8020/api/kb/jobs/${result.job_id}`).then(r => r.json())
         if (job.phase === 'done' || job.phase === 'error') {
           clearInterval(poll); setUploading(false); setProgress(null); loadDocs()
         } else {
           setProgress({ phase: job.phase, progress: job.progress })
         }
       }, 1000)
     } catch (e) { setUploading(false); console.error(e) }
   }
 
   return (
     <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif', maxWidth: 800, margin: '0 auto' }}>
       <div style={{ marginBottom: 24 }}>
         <a href="/" style={{ color: '#666', textDecoration: 'none', fontSize: 14 }}>&larr; Dashboard</a>
         <h1 style={{ fontSize: 20, fontWeight: 600, margin: '4px 0' }}>Knowledge Base</h1>
       </div>
 
       <div style={{ padding: 20, borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff', marginBottom: 20 }}>
         <label style={{ cursor: 'pointer', display: 'block' }}>
           <input type="file" accept=".pdf,.md,.txt" style={{ display: 'none' }}
             onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])} disabled={uploading} />
           <div style={{ padding: 24, borderRadius: 8, border: '2px dashed #d1d5db',
             textAlign: 'center', color: '#6b7280', fontSize: 14 }}>
             {uploading ? 'Uploading...' : 'Click to upload PDF, Markdown, or TXT file'}
           </div>
         </label>
         {progress && <KbUploadProgress phase={progress.phase} progress={progress.progress} />}
       </div>
 
       <KbDocumentList documents={docs} onDelete={(id) => { api.deleteKbDocument(id); loadDocs() }} />
     </div>
   )
 }
