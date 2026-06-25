interface Props { documents: Record<string, unknown>[]; onDelete: (id: string) => void }

export default function KbDocumentList({ documents, onDelete }: Props) {
  if (documents.length === 0) {
    return <p className="text-sm text-text-muted italic">No documents indexed</p>
  }
  return (
    <div className="rounded-xl border border-border overflow-hidden bg-bg-primary">
      {documents.map((doc: any, i) => (
        <div key={doc.id || i}
          className="flex items-center justify-between px-4 py-3 border-b border-border last:border-b-0">
          <div className="min-w-0">
            <div className="text-sm font-medium text-text-primary truncate">{doc.metadata?.source || doc.id}</div>
            <div className="text-xs text-text-muted">ID: {doc.id}</div>
          </div>
          <button onClick={() => onDelete(doc.id)}
            className="px-2.5 py-1 rounded-md border border-danger/30 text-danger bg-danger/5
                       hover:bg-danger/10 transition-colors text-xs flex-shrink-0 ml-3">
            Delete
          </button>
        </div>
      ))}
    </div>
  )
}
