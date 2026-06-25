 interface Props { onClick: () => void }
 export default function TerminateButton({ onClick }: Props) {
   return (
     <button onClick={onClick} title="Terminate execution"
       style={{ padding: '8px 16px', borderRadius: 6, border: '1px solid #fca5a5',
         background: '#fef2f2', color: '#dc2626', cursor: 'pointer', fontSize: 13, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 6 }}>
       <span style={{ fontSize: 16 }}>&#9632;</span> Stop
     </button>
   )
 }
