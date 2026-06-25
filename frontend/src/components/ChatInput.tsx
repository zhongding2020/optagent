import { useState, useRef, useEffect } from 'react'

interface Props {
  onSend: (message: string) => void
  disabled?: boolean
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!disabled) inputRef.current?.focus()
  }, [disabled])

  const handleSend = () => {
    if (value.trim() && !disabled) {
      onSend(value.trim())
      setValue('')
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }

  return (
    <div className="border-t border-border bg-bg-primary">
      <div className="flex items-center gap-2 px-4 py-3 max-w-4xl">
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder={disabled ? 'Waiting for agent...' : 'Type a message...'}
          disabled={disabled}
          className="flex-1 px-4 py-2.5 rounded-xl border border-border bg-bg-secondary
                     text-sm text-text-primary placeholder:text-text-muted outline-none
                     focus:border-accent focus:ring-1 focus:ring-accent/30 transition-all"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className="p-2.5 rounded-xl bg-accent text-white hover:bg-accent-hover
                     disabled:opacity-40 disabled:cursor-not-allowed transition-all
                     flex items-center justify-center"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  )
}
