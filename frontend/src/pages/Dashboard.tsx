 import { useEffect, useState } from 'react'
 import { useNavigate } from 'react-router-dom'
 import { api } from '../hooks/useApi'
 
 export default function Dashboard() {
   const navigate = useNavigate()
   const [workflows, setWorkflows] = useState<{ name: string }[]>([])
   const [sessions, setSessions] = useState<Record<string, unknown>[]>([])
 
   useEffect(() => {
     api.listWorkflows().then(setWorkflows).catch(console.error)
     api.listSessions().then(setSessions).catch(console.error)
   }, [])
 
   const startSession = async (wf: string) => {
     const session = await api.createSession(wf)
     navigate(`/sessions/${session.id}`)
   }
 
   const statusColor: Record<string, string> = {
     pending: '#f59e0b', running: '#3b82f6', completed: '#22c55e',
     error: '#ef4444', interrupted: '#a855f7',
   }
 
   return (
     <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif', maxWidth: 960, margin: '0 auto' }}>
       <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>OptAgent</h1>
       <p style={{ color: '#666', marginBottom: 32 }}>Agent-guided process parameter optimization</p>
 
       <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12 }}>Workflows</h2>
       <div style={{ display: 'flex', gap: 12, marginBottom: 40 }}>
         {workflows.map((wf) => (
           <button key={wf.name} onClick={() => startSession(wf.name)}
             style={{ padding: '12px 24px', borderRadius: 8, border: '1px solid #ddd',
               background: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 500 }}>
             {wf.name}
           </button>
         ))}
       </div>
 
       <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12 }}>Sessions</h2>
       {sessions.length === 0 && <p style={{ color: '#999' }}>No sessions yet</p>}
       <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
         {sessions.map((s: any) => (
           <div key={s.id} onClick={() => navigate(`/sessions/${s.id}`)}
             style={{ padding: 16, borderRadius: 8, border: '1px solid #eee',
               cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
             <div>
               <div style={{ fontWeight: 500 }}>{s.workflow_name}</div>
               <div style={{ fontSize: 12, color: '#999' }}>{s.id?.slice(0, 8)}</div>
             </div>
             <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
               <span style={{ width: 8, height: 8, borderRadius: '50%',
                 background: statusColor[s.status] || '#999', display: 'inline-block' }} />
               <span style={{ fontSize: 13 }}>{s.status}</span>
             </div>
           </div>
         ))}
       </div>
     </div>
   )
 }
