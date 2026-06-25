import { useParams } from 'react-router-dom'
import { useWebSocket } from '../hooks/useWebSocket'
import AgentChat from '../components/AgentChat'
import ChatInput from "../components/ChatInput"
import TerminateButton from '../components/TerminateButton'

export default function Chat() {
  const { id } = useParams<{ id: string }>()
  const { events, connected, send, terminate } = useWebSocket(id || null)

  const messages: { role: string; content: string }[] = []
  let currentToken = ''
  events.forEach((e) => {
    if (e.type === 'user:message') {
      messages.push({ role: 'user', content: e.content })
    }
    else if (e.type === 'agent:token') currentToken += e.content
    else if (e.type === 'agent:message') {
      if (currentToken) { messages.push({ role: 'assistant', content: currentToken }); currentToken = '' }
      messages.push({ role: 'assistant', content: e.content })
    }
  })
  if (currentToken) messages.push({ role: 'assistant', content: currentToken + '...' })

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-bg-primary shrink-0">
        <span className={`text-xs font-medium ${connected ? 'text-success' : 'text-warning'}`}>
          {connected ? 'Connected' : 'Reconnecting...'}
        </span>
        <TerminateButton onClick={terminate} />
      </div>
      <AgentChat messages={messages} />
      <ChatInput onSend={(msg) => send({ type: 'user:message', content: msg })} />
    </div>
  )
}
