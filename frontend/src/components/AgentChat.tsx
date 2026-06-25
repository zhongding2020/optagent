import { useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeHighlight from 'rehype-highlight'

interface Message {
  role: string
  content: string
}

interface Props {
  messages: Message[]
  streaming?: boolean
}

function ChatMessage({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} mb-4`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0
        ${isUser ? 'bg-accent text-white' : 'bg-bg-tertiary text-text-secondary'}`}>
        {isUser ? 'U' : 'A'}
      </div>

      {/* Bubble */}
      <div className={`max-w-[85%] ${isUser ? '' : ''}`}>
        {isUser ? (
          <div className="px-4 py-2.5 rounded-2xl bg-accent text-white text-sm leading-relaxed">
            {msg.content}
          </div>
        ) : (
          <div className="px-4 py-2.5 rounded-2xl bg-bg-secondary text-text-primary text-sm leading-relaxed prose prose-sm max-w-none
            [&_pre]:bg-[#1e1e1e] [&_pre]:text-[#d4d4d4] [&_pre]:p-3 [&_pre]:rounded-lg [&_pre]:overflow-x-auto
            [&_code]:text-[0.85em] [&_p>code]:bg-bg-tertiary [&_p>code]:px-1.5 [&_p>code]:py-0.5 [&_p>code]:rounded
            [&_pre_code]:bg-transparent [&_pre_code]:p-0
            [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_th]:border-border [&_th]:p-2 [&_th]:bg-bg-tertiary
            [&_td]:border [&_td]:border-border [&_td]:p-2
            [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5
            [&_a]:text-accent [&_a]:underline
            [&_blockquote]:border-l-4 [&_blockquote]:border-accent [&_blockquote]:pl-4 [&_blockquote]:text-text-secondary
          ">
            <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
              {msg.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

function ThinkingDots() {
  return (
    <div className="flex gap-3 mb-4">
      <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold bg-bg-tertiary text-text-secondary flex-shrink-0">
        A
      </div>
      <div className="px-4 py-3 rounded-2xl bg-bg-secondary flex items-center gap-1">
        <span className="w-2 h-2 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-2 h-2 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-2 h-2 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  )
}

export default function AgentChat({ messages, streaming }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streaming])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      {messages.length === 0 && !streaming && (
        <div className="h-full flex items-center justify-center">
          <div className="text-center max-w-md">
            <div className="w-12 h-12 rounded-xl bg-accent-light flex items-center justify-center mx-auto mb-4">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                   className="text-accent" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <p className="text-sm text-text-muted">
              Start a conversation with the agent to begin your process optimization workflow.
            </p>
          </div>
        </div>
      )}

      {messages.map((msg, i) => (
        <ChatMessage key={i} msg={msg} />
      ))}

      {streaming && <ThinkingDots />}

      <div ref={bottomRef} />
    </div>
  )
}
