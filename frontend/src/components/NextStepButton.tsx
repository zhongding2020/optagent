interface Props { onClick: () => void }
export default function NextStepButton({ onClick }: Props) {
  return (
    <button onClick={onClick} title="Advance to next step"
      className="px-3 py-1.5 rounded-lg border border-accent/40 bg-accent/5 text-accent
                 hover:bg-accent/10 transition-colors text-xs font-medium">
      Next Step &rarr;
    </button>
  )
}
