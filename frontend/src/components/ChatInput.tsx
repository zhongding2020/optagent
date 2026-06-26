import { useState, useRef, useEffect } from 'react'

interface Props {
  onSend: (message: string) => void
  onUpload?: (file: File) => Promise<void>
  disabled?: boolean
}

export default function ChatInput({ onSend, onUpload, disabled }: Props) {
  const [value, setValue] = useState('')
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

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

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !onUpload) return
    setUploading(true)
    try { await onUpload(file) }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = '' }
  }

  return (
    <div className="border-t border-border bg-bg-primary">
      <div className="flex items-center gap-2 px-4 py-4 mx-auto max-w-3xl">
        {onUpload && (
          <>
            <input type="file" ref={fileRef} hidden onChange={handleFileChange} accept=".csv,.txt" />
            <button onClick={() => fileRef.current?.click()}
              disabled={disabled || uploading}
              className="p-3 rounded-xl text-text-muted hover:text-text-primary hover:bg-bg-hover disabled:opacity-40 transition-all"
              title="Upload CSV file">
              {uploading ? (
                <svg className="animate-spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeDashoffset="8" />
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              )}
            </button>
          </>
        )}
        <input ref={inputRef} type="text" value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
          placeholder={disabled ? 'Waiting for agent...' : 'Send a message...'}
          disabled={disabled}
          className="flex-1 px-4 py-3 rounded-xl border border-border bg-bg-secondary text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-all" />
        <button onClick={handleSend} disabled={disabled || !value.trim()}
          className="p-3 rounded-xl bg-accent text-white hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-all">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  )
}
