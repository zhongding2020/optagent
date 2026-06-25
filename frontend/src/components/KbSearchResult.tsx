 interface Chunk { content: string; metadata: Record<string, string> }
 interface Props { query: string | null; chunks: Chunk[] }
 
 export default function KbSearchResult({ query, chunks }: Props) {
   return (
     <div style={{ padding: 16, borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff' }}>
       <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: '#374151' }}>Knowledge Base</h3>
       {query && <div style={{ fontSize: 12, color: '#3b82f6', marginBottom: 8 }}>Search: "{query}"</div>}
       {chunks.map((chunk, i) => (
         <div key={i} style={{ marginBottom: 8, padding: 8, borderRadius: 6, background: '#f9fafb', fontSize: 12, lineHeight: 1.4 }}>
           <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{chunk.content.slice(0, 200)}</div>
           {chunk.metadata?.source && <div style={{ color: '#9ca3af', marginTop: 4, fontSize: 11 }}>Source: {chunk.metadata.source}</div>}
         </div>
       ))}
       {!query && chunks.length === 0 && <p style={{ fontSize: 13, color: '#9ca3af', fontStyle: 'italic' }}>KB results will appear as the agent searches...</p>}
     </div>
   )
 }
