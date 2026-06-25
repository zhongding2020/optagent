 import { useParams, useNavigate } from 'react-router-dom'
 import { useWebSocket } from '../hooks/useWebSocket'
 import WorkflowGraph from '../components/WorkflowGraph'
 import AgentChat from '../components/AgentChat'
 import SkillStatus from '../components/SkillStatus'
 import TerminateButton from '../components/TerminateButton'
 import NextStepButton from '../components/NextStepButton'
 import KbSearchResult from '../components/KbSearchResult'
 
 const WORKFLOW_NODES = [
   'define_objective', 'identify_params', 'design_doe',
   'collect_data', 'analyze_results', 'generate_report',
 ]
 
 export default function WorkflowDetail() {
   const { id } = useParams<{ id: string }>()
   const navigate = useNavigate()
   const { events, connected, send, terminate, nextStep } = useWebSocket(id || null)
 
   const nodeStatuses: Record<string, string> = {}
   const errors: string[] = []
   let kbQuery: string | null = null
   let kbChunks: { content: string; metadata: Record<string, string> }[] = []
   let chatMessages: { role: string; content: string }[] = []
   let currentToken = ''
 
   events.forEach((e) => {
     if (e.type === 'node:enter') nodeStatuses[e.node] = 'running'
     else if (e.type === 'node:exit') nodeStatuses[e.node] = 'completed'
     else if (e.type === 'node:error') { nodeStatuses[e.node] = 'error'; errors.push(e.error) }
     else if (e.type === 'node:skipped') nodeStatuses[e.node] = 'skipped'
     else if (e.type === 'node:retry') nodeStatuses[e.node] = 'retrying'
     else if (e.type === 'agent:token') currentToken += e.content
     else if (e.type === 'agent:message') {
       if (currentToken) { chatMessages.push({ role: 'assistant', content: currentToken }); currentToken = '' }
       chatMessages.push({ role: 'assistant', content: e.content })
     }
     else if (e.type === 'kb:query') kbQuery = e.query
     else if (e.type === 'kb:result') kbChunks = e.chunks
   })
 
   if (currentToken) chatMessages.push({ role: 'assistant', content: currentToken + '...' })
 
   return (
     <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif', maxWidth: 1200, margin: '0 auto' }}>
       <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
         <div>
           <a href="/" style={{ color: '#666', textDecoration: 'none', fontSize: 14 }}>&larr; Dashboard</a>
           <h1 style={{ fontSize: 20, fontWeight: 600, margin: '4px 0' }}>Session {id?.slice(0, 8)}</h1>
           <span style={{ fontSize: 12, padding: '2px 8px', borderRadius: 4,
             background: connected ? '#d1fae5' : '#fef3c7',
             color: connected ? '#059669' : '#d97706' }}>
             {connected ? 'Connected' : 'Reconnecting...'}
           </span>
         </div>
         <div style={{ display: 'flex', gap: 8 }}>
           <NextStepButton onClick={nextStep} />
           <TerminateButton onClick={terminate} />
           <button onClick={() => navigate(`/sessions/${id}/analysis`)}
             style={{ padding: '8px 16px', borderRadius: 6, border: '1px solid #ddd',
               background: '#fff', cursor: 'pointer', fontSize: 13 }}>Analysis</button>
         </div>
       </div>
 
       <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 20 }}>
         <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
           <WorkflowGraph nodes={WORKFLOW_NODES} statuses={nodeStatuses} durations={{}} />
           <AgentChat messages={chatMessages} />
         </div>
         <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
           <SkillStatus nodeStatuses={nodeStatuses} />
           <KbSearchResult query={kbQuery} chunks={kbChunks} />
         </div>
       </div>
 
       {errors.length > 0 && (
         <div style={{ marginTop: 16, padding: 12, background: '#fef2f2', borderRadius: 8, color: '#dc2626', fontSize: 13 }}>
           {errors.map((e, i) => <div key={i}>{e}</div>)}
         </div>
       )}
     </div>
   )
 }
