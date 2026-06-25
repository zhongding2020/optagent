 import { useParams, useNavigate } from 'react-router-dom'
 import { useWebSocket } from '../hooks/useWebSocket'
 import AgentChat from '../components/AgentChat'
 import TerminateButton from '../components/TerminateButton'
 
 export default function Chat() {
   const { id } = useParams<{ id: string }>()
   const navigate = useNavigate()
   const { events, connected, send, terminate } = useWebSocket(id || null)
 
   const messages: { role: string; content: string }[] = []
   let currentToken = ''
 
   events.forEach((e) => {
     if (e.type === 'agent:token') currentToken += e.content
     else if (e.type === 'agent:message') {
       if (currentToken) { messages.push({ role: 'assistant', content: currentToken }); currentToken = '' }
       messages.push({ role: 'assistant', content: e.content })
     }
   })
 
   if (currentToken) messages.push({ role: 'assistant', content: currentToken + '...' })
 
   return (
     <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif', maxWidth: 800, margin: '0 auto' }}>
       <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
         <a href={`/sessions/${id}`} style={{ color: '#666', textDecoration: 'none', fontSize: 14 }}>&larr; Back to session</a>
         <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
           <span style={{ fontSize: 12, color: connected ? '#059669' : '#d97706' }}>
             {connected ? 'Connected' : 'Reconnecting...'}
           </span>
           <TerminateButton onClick={terminate} />
         </div>
       </div>
       <AgentChat messages={messages} />
     </div>
   )
 }
