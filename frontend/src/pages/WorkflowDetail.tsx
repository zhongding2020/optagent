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
  const chatMessages: { role: string; content: string }[] = []
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
    <div className="h-full flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-bg-primary shrink-0">
        <div className="flex items-center gap-3">
          <a href={`/sessions/${id}/analysis`}
            className="text-xs text-text-muted hover:text-text-secondary transition-colors">Analysis</a>
          <span className="w-1 h-1 rounded-full bg-text-muted" />
          <span className={`text-xs font-medium ${connected ? 'text-success' : 'text-warning'}`}>
            {connected ? 'Connected' : 'Reconnecting...'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <NextStepButton onClick={nextStep} />
          <TerminateButton onClick={terminate} />
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          <AgentChat messages={chatMessages} />
        </div>

        {/* Right sidebar */}
        <div className="w-72 border-l border-border bg-bg-primary flex flex-col overflow-y-auto shrink-0">
          <div className="p-4 border-b border-border">
            <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Workflow</h3>
            <WorkflowGraph nodes={WORKFLOW_NODES} statuses={nodeStatuses} durations={{}} />
          </div>
          <div className="p-4 border-b border-border">
            <SkillStatus nodeStatuses={nodeStatuses} />
          </div>
          <div className="p-4">
            <KbSearchResult query={kbQuery} chunks={kbChunks} />
          </div>
        </div>
      </div>

      {errors.length > 0 && (
        <div className="px-6 py-3 bg-danger/10 border-t border-border shrink-0">
          <div className="text-xs text-danger">{errors.map((e, i) => <div key={i}>{e}</div>)}</div>
        </div>
      )}
    </div>
  )
}
