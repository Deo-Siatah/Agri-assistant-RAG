import { useEffect, useRef, useState } from 'react'
import { 
  Send, 
  Sprout, 
  GraduationCap, 
  Globe, 
  Languages, 
  Bot, 
  User,
  Loader2,
  Info
} from 'lucide-react'

import { askQuestion, type Audience, type Language } from '../lib/api'
import type { County } from '../data/kenyaCounties'

interface ChatPanelProps {
  selectedCounty: County | null
}

interface ChatTurn {
  id: string
  question: string
  answer: string
  audience: Audience
  language: Language
  cacheHit: boolean
  toolsInvoked: string[]
  latencyMs: number
  timestamp: number
}

interface StoredChatState {
  sessionId: string | null
  messages: ChatTurn[]
}

function loadStoredChatState(county: County | null): StoredChatState {
  if (!county) return { sessionId: null, messages: [] }

  const raw = localStorage.getItem(`agri_chat_${county.name}`)
  if (!raw) return { sessionId: null, messages: [] }

  try {
    const parsed = JSON.parse(raw) as Partial<StoredChatState>
    return {
      sessionId: parsed.sessionId ?? null,
      messages: parsed.messages ?? [],
    }
  } catch {
    return { sessionId: null, messages: [] }
  }
}

export default function ChatPanel({ selectedCounty }: ChatPanelProps) {
  const [question, setQuestion] = useState('')
  const [audience, setAudience] = useState<Audience>('farmer')
  const [language, setLanguage] = useState<Language>('en')
  const [messages, setMessages] = useState<ChatTurn[]>(
    () => loadStoredChatState(selectedCounty).messages
  )
  const [sessionId, setSessionId] = useState<string | null>(
    () => loadStoredChatState(selectedCounty).sessionId
  )
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messageListRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const stored = loadStoredChatState(selectedCounty)
    setMessages(stored.messages)
    setSessionId(stored.sessionId)
  }, [selectedCounty])

  useEffect(() => {
    if (!selectedCounty) return
    const toStore: StoredChatState = { sessionId, messages }
    localStorage.setItem(`agri_chat_${selectedCounty.name}`, JSON.stringify(toStore))
  }, [messages, sessionId, selectedCounty])

  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight
    }
  }, [messages, isLoading])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!selectedCounty) {
      setError('Please select a county first')
      return
    }

    const trimmedQuestion = question.trim()
    if (!trimmedQuestion) return

    setIsLoading(true)
    setError(null)

    try {
      const startedAt = performance.now()
      const response = await askQuestion({
        question: trimmedQuestion,
        lat: selectedCounty.lat,
        lon: selectedCounty.lon,
        audience,
        language,
        session_id: sessionId,
      })

      const latencyMs =
        typeof response.latency_ms === 'number'
          ? response.latency_ms
          : Math.max(0, Math.round(performance.now() - startedAt))

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: crypto.randomUUID(),
          question: trimmedQuestion,
          answer: response.answer,
          audience,
          language,
          cacheHit: response.cache_hit,
          toolsInvoked: response.tools_invoked,
          latencyMs,
          timestamp: Date.now(),
        },
      ])
      setSessionId(response.session_id)
      setQuestion('')
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : 'An unexpected error occurred'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

        .chat-wrapper {
          --primary: #0F172A;
          --primary-hover: #1E293B;
          --surface: #FFFFFF;
          --background: #F8FAFC;
          --border: #E2E8F0;
          --text-main: #0F172A;
          --text-muted: #64748B;
          --accent: #10B981;
          
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          height: 100dvh;
          background: var(--background);
        }

        .chat-container {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          background: var(--surface);
          position: relative;
          overflow: hidden;
        }

        .chat-header {
          padding: 1rem 1.5rem;
          background: var(--surface);
          border-bottom: 1px solid var(--border);
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
          justify-content: space-between;
          align-items: center;
          z-index: 10;
        }

        .toggle-group {
          display: flex;
          background: var(--background);
          padding: 4px;
          border-radius: 12px;
          border: 1px solid var(--border);
        }

        .toggle-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 14px;
          border-radius: 8px;
          border: none;
          background: transparent;
          color: var(--text-muted);
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          font-family: inherit;
        }

        .toggle-btn:hover {
          color: var(--text-main);
        }

        .toggle-btn.active {
          background: var(--surface);
          color: var(--primary);
          box-shadow: 0 2px 4px rgba(0,0,0,0.06);
        }

        .chat-body {
          flex-grow: 1;
          padding: 1rem;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          scroll-behavior: smooth;
        }

        .chat-body::-webkit-scrollbar {
          display: none;
        }
        .chat-body {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }

        .message-row {
          display: flex;
          gap: 8px;
          max-width: 95%;
        }

        .message-row.user {
          align-self: flex-end;
          flex-direction: row-reverse;
        }

        .message-row.bot {
          align-self: flex-start;
        }

        @media (min-width: 768px) {
          .chat-container {
            width: 100%;
            max-width: 900px;
            height: 90vh;
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
            border: 1px solid var(--border);
          }
          
          .chat-body {
            padding: 1.5rem;
          }
          
          .message-row {
            gap: 12px;
            max-width: 85%;
          }
        }

        .avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .avatar.user {
          background: var(--primary);
          color: white;
        }

        .avatar.bot {
          background: var(--accent);
          color: white;
          box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
        }

        .bubble {
          padding: 14px 18px;
          font-size: 15px;
          line-height: 1.6;
          word-break: break-word;
          white-space: pre-wrap;
        }

        .bubble.user {
          background: var(--primary);
          color: white;
          border-radius: 20px 20px 4px 20px;
          box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
        }

        .bubble.bot {
          background: var(--surface);
          color: var(--text-main);
          border: 1px solid var(--border);
          border-radius: 20px 20px 20px 4px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        }

        .meta-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 8px;
          align-items: center;
        }

        .meta-badge {
          border-radius: 999px;
          padding: 2px 10px;
          font-size: 11px;
          font-weight: 500;
          display: inline-flex;
          align-items: center;
          background: var(--background);
          color: var(--text-muted);
          border: 1px solid var(--border);
        }

        .meta-badge.highlight {
          background: rgba(16, 185, 129, 0.1);
          color: var(--accent);
          border-color: rgba(16, 185, 129, 0.2);
        }

        .chat-footer {
          padding: 1.25rem 1.5rem;
          background: var(--surface);
          border-top: 1px solid var(--border);
        }

        .input-wrapper {
          display: flex;
          gap: 12px;
          align-items: center;
          background: var(--background);
          padding: 6px 6px 6px 20px;
          border-radius: 999px;
          border: 1px solid var(--border);
          transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .input-wrapper:focus-within {
          border-color: var(--primary);
          box-shadow: 0 0 0 3px rgba(15, 23, 42, 0.05);
        }

        .chat-input {
          flex-grow: 1;
          background: transparent;
          border: none;
          outline: none;
          font-size: 15px;
          color: var(--text-main);
          font-family: inherit;
        }

        .chat-input::placeholder {
          color: var(--text-muted);
        }

        .send-btn {
          width: 44px;
          height: 44px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--primary);
          color: white;
          border: none;
          cursor: pointer;
          transition: all 0.2s ease;
          flex-shrink: 0;
        }

        .send-btn:hover:not(:disabled) {
          background: var(--primary-hover);
          transform: scale(1.05);
        }

        .send-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .empty-state {
          margin: auto;
          text-align: center;
          color: var(--text-muted);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin {
          animation: spin 1s linear infinite;
        }
      `}</style>

      <section className="chat-wrapper">
        <div className="chat-container">
          
          {/* Header & Controls */}
          <header className="chat-header">
            <div className="toggle-group">
              <button
                type="button"
                onClick={() => setAudience('farmer')}
                className={`toggle-btn ${audience === 'farmer' ? 'active' : ''}`}
              >
                <Sprout size={16} /> Farmer
              </button>
              <button
                type="button"
                onClick={() => setAudience('expert')}
                className={`toggle-btn ${audience === 'expert' ? 'active' : ''}`}
              >
                <GraduationCap size={16} /> Expert
              </button>
            </div>

            <div className="toggle-group">
              <button
                type="button"
                onClick={() => setLanguage('en')}
                className={`toggle-btn ${language === 'en' ? 'active' : ''}`}
              >
                <Languages size={16} /> EN
              </button>
              <button
                type="button"
                onClick={() => setLanguage('sw')}
                className={`toggle-btn ${language === 'sw' ? 'active' : ''}`}
              >
                <Globe size={16} /> SW
              </button>
            </div>
          </header>

          {/* Chat Area */}
          <div className="chat-body" ref={messageListRef}>
            {messages.length === 0 ? (
              <div className="empty-state">
                <div style={{ padding: '16px', background: 'var(--background)', borderRadius: '50%' }}>
                  <Sprout size={32} color="var(--accent)" />
                </div>
                <h3 style={{ margin: 0, fontWeight: 600, color: 'var(--text-main)' }}>
                  {selectedCounty ? `Welcome to ${selectedCounty.name}` : 'Ready to help'}
                </h3>
                <p style={{ margin: 0, fontSize: 14 }}>
                  {selectedCounty 
                    ? 'Ask any agricultural question for this region.' 
                    : 'Please select a county to get started.'}
                </p>
              </div>
            ) : null}

            {messages.map((message) => (
              <div key={message.id} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                
                {/* User Message */}
                <div className="message-row user">
                  <div className="avatar user">
                    <User size={20} />
                  </div>
                  <div className="bubble user">{message.question}</div>
                </div>

                {/* Bot Response */}
                <div className="message-row bot">
                  <div className="avatar bot">
                    <Bot size={20} />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                    <div className="bubble bot">{message.answer}</div>
                    
                    {/* Metadata Badges */}
                    <div className="meta-tags">
                      <span className={`meta-badge ${message.cacheHit ? 'highlight' : ''}`}>
                        {message.cacheHit ? '⚡ Instant (Cached)' : '🔄 Freshly Generated'}
                      </span>
                      <span className="meta-badge">{message.latencyMs}ms</span>
                      {message.toolsInvoked.map((toolName) => (
                        <span key={`${message.id}-${toolName}`} className="meta-badge">
                          {toolName}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message-row bot" style={{ animation: 'pulse 1.5s infinite' }}>
                <div className="avatar bot">
                  <Loader2 size={20} className="spin" />
                </div>
                <div className="bubble bot" style={{ color: 'var(--text-muted)' }}>
                  Analyzing data for {selectedCounty?.name}...
                </div>
              </div>
            )}
          </div>

          {/* Error Banner */}
          {error && (
            <div style={{
              margin: '0 1.5rem',
              padding: '12px 16px',
              background: '#FEF2F2',
              border: '1px solid #FCA5A5',
              color: '#DC2626',
              borderRadius: '12px',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Info size={16} />
              {error}
            </div>
          )}

          {/* Input Area */}
          <footer className="chat-footer">
            <form onSubmit={handleSubmit}>
              <div className="input-wrapper">
                <input
                  type="text"
                  className="chat-input"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder={selectedCounty ? `Ask about farming in ${selectedCounty.name}...` : 'Select a county first...'}
                  disabled={isLoading || !selectedCounty}
                />
                <button
                  type="submit"
                  className="send-btn"
                  disabled={isLoading || question.trim().length === 0 || !selectedCounty}
                  aria-label="Send question"
                >
                  <Send size={18} strokeWidth={2.5} />
                </button>
              </div>
            </form>
          </footer>

        </div>
      </section>
    </>
  )
}