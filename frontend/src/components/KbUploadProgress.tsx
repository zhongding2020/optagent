interface Props { phase: string; progress: number }

const labels: Record<string, string> = {
  loading: 'Loading file...', splitting: 'Splitting document...',
  embedding: 'Embedding chunks...', done: 'Complete!',
}

export default function KbUploadProgress({ phase, progress }: Props) {
  return (
    <div className="mt-3">
      <div className="text-xs text-text-secondary mb-1">{labels[phase] || phase}</div>
      <div className="h-1.5 rounded-full bg-bg-tertiary overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500
          ${phase === 'done' ? 'bg-success' : 'bg-accent'}`}
          style={{ width: `${progress * 100}%` }} />
      </div>
    </div>
  )
}
