 interface Props { nodeStatuses: Record<string, string> }
 
 const LABELS: Record<string, string> = {
   define_objective: 'Define Objective', identify_params: 'Identify Parameters',
   design_doe: 'Design DOE', collect_data: 'Collect Data',
   analyze_results: 'Analyze Results', generate_report: 'Generate Report',
 }
 
 export default function SkillStatus({ nodeStatuses }: Props) {
   const active = Object.entries(nodeStatuses).find(([, s]) => s === 'running')
   return (
     <div style={{ padding: 16, borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff' }}>
       <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: '#374151' }}>Skill Status</h3>
       {active ? (
         <div style={{ fontSize: 13, color: '#3b82f6', fontWeight: 500 }}>Active: {LABELS[active[0]] || active[0]}</div>
       ) : <p style={{ fontSize: 13, color: '#9ca3af' }}>Waiting...</p>}
       <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
         {Object.entries(nodeStatuses).map(([node, status]) => (
           <div key={node} style={{ fontSize: 12, display: 'flex', justifyContent: 'space-between' }}>
             <span>{LABELS[node] || node}</span>
             <span style={{ color: status === 'completed' ? '#22c55e' : status === 'error' ? '#ef4444' : '#9ca3af' }}>{status}</span>
           </div>
         ))}
       </div>
     </div>
   )
 }
