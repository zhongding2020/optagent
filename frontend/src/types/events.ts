export type WSEvent =
  | { type: 'graph:start'; session_id: string; workflow_name: string; nodes: string[] }
  | { type: 'graph:end'; session_id: string }
  | { type: 'graph:error'; error: string }
  | { type: 'graph:interrupted'; session_id: string; reason?: string }
  | { type: 'node:enter'; node: string }
  | { type: 'node:exit'; node: string; duration_ms: number }
  | { type: 'node:progress'; current_node: string; completed_nodes: string[] }
  | { type: 'node:error'; node: string; error: string; recoverable?: boolean }
  | { type: 'node:retry'; node: string; attempt: number; max: number }
  | { type: 'node:skipped'; node: string; error?: string }
  | { type: 'agent:message'; content: string }
  | { type: 'agent:token'; content: string }
  | { type: 'agent:tool_call'; tool: string; args: Record<string, unknown> }
  | { type: 'agent:tool_result'; tool: string; output: string }
  | { type: 'agent:thinking' }
  | { type: 'skill:matched'; skill: string }
  | { type: 'kb:query'; query: string; top_k?: number }
  | { type: 'kb:result'; chunks: Array<{ content: string; metadata: Record<string, string> }> }
  | { type: 'kb:index_progress'; job_id: string; phase: string; progress: number; documents: number | null }
  | { type: 'ping' }
