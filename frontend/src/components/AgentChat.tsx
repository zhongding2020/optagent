 import { useRef, useEffect } from 'react'
 
 interface Message { role: string; content: string }
 interface Props { messages: Message[] }
 
 export default function AgentChat({ messages }: Props) {
   const bottomRef = useRef<HTMLDivElement>(null)
   useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
 
   return (
     <div style={{ padding: 20, borderRadius: 8, border: '1px solid #e5e7eb', background: '#fff', maxHeight: 400, overflowY: 'auto' }}>
       <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: '#374151' }}>Agent Chat</h3>
       {messages.length === 0 && <p style={{ color: '#9ca3af', fontSize: 13, fontStyle: 'italic' }}>Agent conversation will appear here...</p>}
       {messages.map((msg, i) => (
         <div key={i} style={{ marginBottom: 8, padding: '8px 12px', borderRadius: 8,
           background: msg.role === 'assistant' ? '#f3f4f6' : '#eff6ff', maxWidth: '90%' }}>
           <div style={{ fontSize: 13, lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{msg.content}</div>
         </div>
       ))}
       <div ref={bottomRef} />
     </div>
   )
 }
