import { useParams, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import { api } from '../hooks/useApi'
import WorkflowGraph from '../components/WorkflowGraph'
import AgentChat from '../components/AgentChat'
import SkillStatus from '../components/SkillStatus'
import TerminateButton from '../components/TerminateButton'
import NextStepButton from '../components/NextStepButton'
import ChatInput from "../components/ChatInput"
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
  const durations: Record<string, number> = {}
  const errors: string[] = []
  let kbQuery: string | null = null
  let kbChunks: { content: string; metadata: Record<string, string> }[] = []
  const chatMessages: { role: string; content: string }[] = []
  let currentToken = ''
  const matchedSkills: string[] = []
  let workflowComplete = false
  const [initialHistory, setInitialHistory] = useState<{ role: string; content: string }[]>([])
  let pendingCharts: { chartType: string; data: Record<string, any>; label?: string }[] = []
  let tokenStats = { input: 0, output: 0 }
 const ANALYSIS_TOOLS: Record<string, string> = {
    factor_importance: 'factor_importance',
    correlation_analysis: 'correlation_analysis',
    pareto_analysis: 'pareto_analysis',
    response_surface: 'response_surface',
    design_experiment: 'design_experiment',
    anova_one_way: 'anova_one_way',
  }

  events.forEach((e) => {
    if (e.type === 'node:enter') nodeStatuses[e.node] = 'running'
    else if (e.type === 'node:exit') { 
      nodeStatuses[e.node] = 'completed'
      if (e.duration_ms) durations[e.node] = e.duration_ms
    }
    else if (e.type === 'node:error') { nodeStatuses[e.node] = 'error'; errors.push(e.error) }
    else if (e.type === 'node:skipped') nodeStatuses[e.node] = 'skipped'
    else if (e.type === 'node:retry') nodeStatuses[e.node] = 'retrying'
    else if (e.type === 'agent:token') currentToken += e.content
    else if (e.type === 'agent:message') {
      const msg: any = { role: 'assistant', content: e.content }
      if (pendingCharts.length > 0) {
        msg.charts = [...pendingCharts]
        pendingCharts = []
      }
      chatMessages.push(msg)
      currentToken = ''
    }
    else if (e.type === 'user:message') {
      chatMessages.push({ role: 'user', content: e.content })
    }
    else if (e.type === 'skill:matched') {
      if (!matchedSkills.includes(e.skill)) matchedSkills.push(e.skill)
    }
    else if (e.type === 'kb:query') kbQuery = e.query
    else if (e.type === 'kb:result') kbChunks = e.chunks
    else if (e.type === 'agent:tool_result') {
      const chartType = ANALYSIS_TOOLS[e.tool as string]
      if (chartType) {
        try {
          const parsed = JSON.parse(e.output as string)
          if (parsed && !parsed.error) {
            const labels: Record<string, string> = {
              factor_importance: 'Factor Importance Ranking',
              correlation_analysis: 'Correlation Analysis',
              pareto_analysis: 'Pareto Analysis',
              response_surface: 'Response Surface Model',
              design_experiment: 'DOE Design',
              anova_one_way: 'ANOVA Analysis',
            }
            pendingCharts.push({ chartType, data: parsed, label: labels[chartType] || '' })
          }
        } catch {}
      }
    }
    else if (e.type === 'agent:stats') {
      tokenStats = { input: e.session_input_total, output: e.session_output_total }
    }
    else if (e.type === 'graph:end') workflowComplete = true
  })
  if (currentToken) chatMessages.push({ role: 'assistant', content: currentToken + '...' })

  useEffect(() => {
    if (!id) return
    api.getSessionMessages(id).then((res: any) => {
      if (res?.messages) setInitialHistory(res.messages.map((m: any) => ({ role: m.role, content: m.content })))
    }).catch(() => {})
  }, [id])

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
          {workflowComplete && (
            <span className="text-xs font-medium text-success">Workflow Complete</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {(tokenStats.input > 0 || tokenStats.output > 0) && (
            <div className="flex items-center gap-1 text-[10px] text-text-muted font-mono">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
              <span>{tokenStats.input}→{tokenStats.output}</span>
            </div>
          )}
          <NextStepButton onClick={nextStep} />
          <TerminateButton onClick={terminate} />
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          <AgentChat messages={[...initialHistory, ...chatMessages]} />
          <ChatInput onSend={(msg) => send({ type: 'user:message', content: msg })} />
        </div>

        {/* Right sidebar */}
        <div className="w-72 border-l border-border bg-bg-primary flex flex-col overflow-y-auto shrink-0">
          <div className="p-4 border-b border-border">
            <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Workflow</h3>
            <WorkflowGraph nodes={WORKFLOW_NODES} statuses={nodeStatuses} durations={durations} />
          </div>
          <div className="p-4 border-b border-border">
            <SkillStatus nodeStatuses={nodeStatuses} matchedSkills={matchedSkills} />
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
