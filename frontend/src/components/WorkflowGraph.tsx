interface Props { nodes: string[]; statuses: Record<string, string>; durations: Record<string, number> }

const colors: Record<string, string> = {
  pending: 'bg-border',
  running: 'bg-accent',
  completed: 'bg-success',
  error: 'bg-danger',
  skipped: 'bg-warning',
  retrying: 'bg-warning',
}

const labels: Record<string, string> = {
  define_objective: 'Define Objective', identify_params: 'Identify Parameters',
  design_doe: 'Design DOE', collect_data: 'Collect Data',
  analyze_results: 'Analyze Results', generate_report: 'Generate Report',
}

export default function WorkflowGraph({ nodes, statuses, durations }: Props) {
  return (
    <div className="flex flex-col gap-0.5">
      {nodes.map((node, i) => {
        const s = statuses[node] || 'pending'
        return (
          <div key={node}>
            <div className={`flex items-center gap-2.5 px-2 py-1.5 rounded-md
              ${s === 'running' ? 'bg-accent/5' : ''}`}>
              <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 transition-colors ${colors[s] || colors.pending}`} />
              <span className={`text-xs font-medium flex-1 ${s === 'running' ? 'text-accent' : 'text-text-secondary'}`}>
                {labels[node] || node}
              </span>
              {durations[node] && (
                <span className="text-[10px] text-text-muted">{(durations[node] / 1000).toFixed(1)}s</span>
              )}
            </div>
            {i < nodes.length - 1 && (
              <div className={`ml-[11px] w-0.5 h-3 ${s === 'completed' ? 'bg-success' : 'bg-border'}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
