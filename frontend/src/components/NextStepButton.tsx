 interface Props { onClick: () => void }
 export default function NextStepButton({ onClick }: Props) {
   return (
     <button onClick={onClick} title="Advance to next step"
       style={{ padding: '8px 16px', borderRadius: 6, border: '1px solid #93c5fd',
         background: '#eff6ff', color: '#2563eb', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}>
       Next Step &rarr;
     </button>
   )
 }
