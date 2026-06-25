interface Chunk { content: string; metadata: Record<string, string> }
interface Props { query: string | null; chunks: Chunk[] }

export default function KbSearchResult({ query, chunks }: Props) {
  return (
    <div>
      <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Knowledge Base</h4>
      {query && <div className="text-[11px] text-accent mb-2 truncate">Search: "{query}"</div>}
      {chunks.map((chunk, i) => (
        <div key={i} className="mb-2 p-2 rounded-lg bg-bg-tertiary">
          <div className="text-[11px] leading-relaxed text-text-secondary line-clamp-3">{chunk.content}</div>
          {chunk.metadata?.source && (
            <div className="text-[10px] text-text-muted mt-1 truncate">{chunk.metadata.source}</div>
          )}
        </div>
      ))}
      {!query && chunks.length === 0 && (
        <p className="text-[11px] text-text-muted italic">KB results will appear as the agent searches...</p>
      )}
    </div>
  )
}
