 interface Props { documents: Record<string, unknown>[]; onDelete: (id: string) => void }
 export default function KbDocumentList({ documents, onDelete }: Props) {
   if (documents.length === 0) return <p style={{ color: '#9ca3af', fontSize: 13, fontStyle: 'italic' }}>No documents indexed</p>
   return (
     <div style={{ borderRadius: 8, border: '1px solid #e5e7eb', overflow: 'hidden' }}>
       {documents.map((doc: any, i) => (
         <div key={doc.id || i} style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between',
           alignItems: 'center', borderBottom: i < documents.length - 1 ? '1px solid #f3f4f6' : 'none' }}>
           <div>
             <div style={{ fontSize: 13, fontWeight: 500 }}>{doc.metadata?.source || doc.id}</div>
             <div style={{ fontSize: 11, color: '#9ca3af' }}>ID: {doc.id}</div>
           </div>
           <button onClick={() => onDelete(doc.id)} style={{ padding: '4px 12px', borderRadius: 4,
             border: '1px solid #fca5a5', background: '#fef2f2', color: '#dc2626', cursor: 'pointer', fontSize: 12 }}>
             Delete
           </button>
         </div>
       ))}
     </div>
   )
 }
