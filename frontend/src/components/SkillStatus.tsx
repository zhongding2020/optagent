interface Props {
  nodeStatuses: Record<string, string>
  matchedSkills?: string[]
}

const LABELS: Record<string, string> = {
  define_objective: 'Define Objective', identify_params: 'Identify Parameters',
  design_doe: 'Design DOE', collect_data: 'Collect Data',
  analyze_results: 'Analyze Results', generate_report: 'Generate Report',
}

export default function SkillStatus({ nodeStatuses, matchedSkills }: Props) {
  const hasMatched = matchedSkills && matchedSkills.length > 0
  const active = Object.entries(nodeStatuses).find(([, s]) => s === 'running')
  return (
    <div>
      <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Skills</h4>

      {hasMatched && (
        <div className="mb-2">
          <div className="text-[11px] text-accent font-medium mb-1">Matched for this message:</div>
          <div className="flex flex-wrap gap-1">
            {matchedSkills!.map((s) => (
              <span key={s} className="px-2 py-0.5 rounded-full bg-accent-light/20 text-accent text-[10px] font-medium border border-accent/30">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {active ? (
        <div className="text-xs text-accent font-medium mb-2">Active: {LABELS[active[0]] || active[0]}</div>
      ) : (
        !hasMatched && <p className="text-xs text-text-muted mb-2">Waiting...</p>
      )}
      <div className="flex flex-col gap-1">
        {Object.entries(nodeStatuses).map(([node, st]) => (
          <div key={node} className="flex justify-between text-[11px]">
            <span className="text-text-secondary">{LABELS[node] || node}</span>
            <span className={`${
              st === 'completed' ? 'text-success' : st === 'error' ? 'text-danger' : 'text-text-muted'
            }`}>{st}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
