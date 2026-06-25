 interface Props { nodes: string[]; statuses: Record<string, string>; durations: Record<string, number> }
 
 const STATUS_COLORS: Record<string, string> = {
   pending: '#e5e7eb', running: '#3b82f6', completed: '#22c55e',
   error: '#ef4444', skipped: '#f59e0b', retrying: '#f59e0b',
 }
 
 const NODE_LABELS: Record<string, string> = {
   define_objective: 'Define\nObjective', identify_params: 'Identify\nParameters',
   design_doe: 'Design\nDOE', collect_data: 'Collect\nData',
   analyze_results: 'Analyze\nResults', generate_report: 'Generate\nReport',
 }
 
 export default function WorkflowGraph({ nodes, statuses, durations }: Props) {
   return (
     <div style={{ padding: 20, borderRadius: 8, border: '1px solid #e5e7eb', background: '#fafafa' }}>
       <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: '#374151' }}>Workflow Progress</h3>
       <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
         {nodes.map((node, i) => (
           <div key={node}>
             <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 12px', borderRadius: 6,
               background: statuses[node] === 'running' ? '#eff6ff' : 'transparent' }}>
               <div style={{ width: 12, height: 12, borderRadius: '50%', flexShrink: 0,
                 background: STATUS_COLORS[statuses[node]] || STATUS_COLORS.pending }} />
               <div style={{ fontSize: 13, fontWeight: 500, whiteSpace: 'pre-line', flex: 1 }}>
                 {NODE_LABELS[node] || node}
               </div>
               {durations[node] && <span style={{ fontSize: 11, color: '#9ca3af' }}>{(durations[node] / 1000).toFixed(1)}s</span>}
               <span style={{ fontSize: 11, color: '#9ca3af', textTransform: 'capitalize' }}>{statuses[node] || 'pending'}</span>
             </div>
             {i < nodes.length - 1 && <div style={{ marginLeft: 17, width: 2, height: 16,
               background: statuses[node] === 'completed' ? '#22c55e' : '#e5e7eb' }} />}
           </div>
         ))}
       </div>
     </div>
   )
 }
