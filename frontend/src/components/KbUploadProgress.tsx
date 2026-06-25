 interface Props { phase: string; progress: number }
 const PHASE_LABELS: Record<string, string> = {
   loading: 'Loading file...', splitting: 'Splitting document...',
   embedding: 'Embedding chunks...', done: 'Complete!',
 }
 export default function KbUploadProgress({ phase, progress }: Props) {
   return (
     <div style={{ marginTop: 12 }}>
       <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>{PHASE_LABELS[phase] || phase}</div>
       <div style={{ height: 6, borderRadius: 3, background: '#e5e7eb', overflow: 'hidden' }}>
         <div style={{ height: '100%', borderRadius: 3, background: phase === 'done' ? '#22c55e' : '#3b82f6',
           width: `${progress * 100}%`, transition: 'width 0.5s' }} />
       </div>
     </div>
   )
 }
