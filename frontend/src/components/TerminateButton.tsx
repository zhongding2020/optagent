interface Props { onClick: () => void }
export default function TerminateButton({ onClick }: Props) {
  return (
    <button onClick={onClick} title="Terminate execution"
      className="px-3 py-1.5 rounded-lg border border-danger/40 bg-danger/5 text-danger
                 hover:bg-danger/10 transition-colors text-xs font-medium flex items-center gap-1.5">
      <span className="text-xs">&#9632;</span> Stop
    </button>
  )
}
