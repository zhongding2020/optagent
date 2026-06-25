import { useParams } from 'react-router-dom'
import { useWebSocket } from '../hooks/useWebSocket'
import AgentChat from '../components/AgentChat'
import KbSearchResult from '../components/KbSearchResult'
import ChatInput from "../components/ChatInput"
import TerminateButton from '../components/TerminateButton'

export default function Chat() {
  const { id } = useParams<{ id: string }>()
  const { events, connected, send, terminate } = useWebSocket(id || null)

  const messages: { role: string; content: string }[] = []
  let currentToken = ''
  const matchedSkills: string[] = []
  let kbQuery: string | null = null
  let kbChunks: { content: string; metadata: Record<string, string> }[] = []
  events.forEach((e) => {
    if (e.type === 'user:message') {
      messages.push({ role: 'user', content: e.content })
    }
    else if (e.type === 'agent:token') currentToken += e.content
    else if (e.type === 'agent:message') {
      currentToken = ''
      messages.push({ role: 'assistant', content: e.content })
    }
    else if (e.type === 'skill:matched') {
      if (!matchedSkills.includes(e.skill)) matchedSkills.push(e.skill)
    }
    else if (e.type === 'kb:query') kbQuery = e.query
    else if (e.type === 'kb:result') kbChunks = e.chunks
  })
  if (currentToken) messages.push({ role: 'assistant', content: currentToken + '...' })

  return (
    <div className="h-full flex flex-col">
      {matchedSkills.length > 0 && (
        <div className="flex items-center gap-2 px-6 py-2 border-b border-border bg-accent-light/5 shrink-0">
          <span className="text-[11px] text-text-muted">Matched skills:</span>
          {matchedSkills.map((s) => (
            <span key={s} className="px-2 py-0.5 rounded-full bg-accent-light/20 text-accent text-[10px] font-medium border border-accent/30">
              {s}
            </span>
          ))}
        </div>
      )}
      <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-bg-primary shrink-0">
        <span className={`text-xs font-medium ${connected ? 'text-success' : 'text-warning'}`}>
          {connected ? 'Connected' : 'Reconnecting...'}
        </span>
        <TerminateButton onClick={terminate} />
      </div>

      {(kbQuery || kbChunks.length > 0) && (
        <div className="border-b border-border bg-bg-primary shrink-0">
          <details className="px-6 py-2" open>
            <summary className="text-[11px] text-text-muted cursor-pointer select-none">
              Knowledge Base {kbChunks.length > 0 ? `(${kbChunks.length} results)` : ''}
            </summary>
            <div className="mt-1 space-y-2">
              <KbSearchResult query={kbQuery} chunks={kbChunks} />
            </div>
          </details>
        </div>
      )}

      <AgentChat messages={messages} />
      <ChatInput onSend={(msg) => send({ type: 'user:message', content: msg })} />
    </div>
  )
}
