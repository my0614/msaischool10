import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send } from 'lucide-react'

const API = `http://${window.location.hostname}:8000`

const GREETING = '안녕 👋 나 비밀 친구야. 오늘 하루 어땠어?'

export default function Chatbot() {
  const [open, setOpen]       = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: GREETING }
  ])
  const [input, setInput]     = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef             = useRef(null)
  const inputRef              = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 300)
  }, [open])

  async function send() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')

    const userMsg = { role: 'user', content: text }
    const next    = [...messages, userMsg]
    setMessages(next)
    setLoading(true)

    try {
      const res  = await fetch(`${API}/api/chat`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ messages: next }),
      }).then(r => r.json())

      setMessages(prev => [...prev, {
        role:    'assistant',
        content: res.reply || res.error || '...',
      }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '연결이 끊겼어 😢' }])
    } finally {
      setLoading(false)
    }
  }

  function onKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <>
      {/* 플로팅 버튼 */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.93 }}
        onClick={() => setOpen(o => !o)}
        style={s.fab}
        title="비밀 친구와 대화하기"
      >
        <AnimatePresence mode="wait">
          {open
            ? <motion.span key="x" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ opacity: 0 }} style={{ lineHeight: 1 }}><X size={22} /></motion.span>
            : <motion.span key="chat" initial={{ scale: 0.7, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ opacity: 0 }} style={{ fontSize: 24 }}>🤫</motion.span>
          }
        </AnimatePresence>
      </motion.button>

      {/* 사이드 패널 */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ x: 380, opacity: 0 }}
            animate={{ x: 0,   opacity: 1 }}
            exit={{   x: 380, opacity: 0 }}
            transition={{ type: 'spring', damping: 28, stiffness: 280 }}
            style={s.panel}
          >
            {/* 헤더 */}
            <div style={s.header}>
              <div style={s.headerLeft}>
                <span style={s.avatar}>🤫</span>
                <div>
                  <p style={s.name}>비밀 친구</p>
                  <p style={s.status}>항상 여기 있어</p>
                </div>
              </div>
              <button onClick={() => setOpen(false)} style={s.closeBtn}><X size={18} /></button>
            </div>

            {/* 메시지 영역 */}
            <div style={s.messages}>
              {messages.map((m, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 }}
                  style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: 12 }}
                >
                  {m.role === 'assistant' && <span style={s.botAvatar}>🤫</span>}
                  <div style={m.role === 'user' ? s.userBubble : s.botBubble}>
                    {m.content}
                  </div>
                </motion.div>
              ))}
              {loading && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <span style={s.botAvatar}>🤫</span>
                  <div style={s.botBubble}>
                    <motion.span
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.2, repeat: Infinity }}
                    >···</motion.span>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* 입력창 */}
            <div style={s.inputRow}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKey}
                placeholder="오늘 어떤 하루였어?"
                rows={1}
                style={s.textarea}
              />
              <motion.button
                whileHover={{ scale: 1.08 }} whileTap={{ scale: 0.93 }}
                onClick={send}
                disabled={!input.trim() || loading}
                style={{ ...s.sendBtn, opacity: (!input.trim() || loading) ? 0.4 : 1 }}
              >
                <Send size={16} />
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

const s = {
  fab: {
    position: 'fixed', bottom: 32, right: 32, zIndex: 200,
    width: 56, height: 56, borderRadius: '50%',
    background: 'linear-gradient(135deg,#4a2c1a,#8b6340)',
    border: '1px solid rgba(196,168,130,0.3)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
    cursor: 'pointer', color: '#f5ebe0',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },

  panel: {
    position: 'fixed', right: 0, top: 0, bottom: 0, zIndex: 150,
    width: 360,
    background: 'linear-gradient(180deg,#1e0f08 0%,#160c06 100%)',
    borderLeft: '1px solid rgba(196,168,130,0.15)',
    boxShadow: '-12px 0 48px rgba(0,0,0,0.5)',
    display: 'flex', flexDirection: 'column',
  },

  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '20px 20px 16px',
    borderBottom: '1px solid rgba(196,168,130,0.1)',
    background: 'rgba(196,168,130,0.04)',
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: 12 },
  avatar:  { fontSize: 36 },
  name:    { color: '#f0e0cc', fontSize: 15, fontWeight: 500, fontFamily: "'Noto Sans KR',sans-serif", margin: 0 },
  status:  { color: '#5a4a42', fontSize: 11, fontFamily: "'Noto Sans KR',sans-serif", marginTop: 2 },
  closeBtn: {
    background: 'transparent', border: 'none', cursor: 'pointer',
    color: '#6a5a52', padding: 4,
  },

  messages: {
    flex: 1, overflowY: 'auto', padding: '20px 16px',
    display: 'flex', flexDirection: 'column',
  },

  botAvatar: { fontSize: 22, marginRight: 8, flexShrink: 0, alignSelf: 'flex-end', marginBottom: 2 },

  botBubble: {
    background: 'rgba(196,168,130,0.1)',
    border: '1px solid rgba(196,168,130,0.18)',
    borderRadius: '18px 18px 18px 4px',
    padding: '10px 14px',
    color: '#e8d5c0', fontSize: 14, lineHeight: 1.7,
    maxWidth: 230, fontFamily: "'Noto Sans KR',sans-serif",
    whiteSpace: 'pre-wrap',
  },
  userBubble: {
    background: 'linear-gradient(135deg,#6b4423,#8b5e35)',
    borderRadius: '18px 18px 4px 18px',
    padding: '10px 14px',
    color: '#fff5e8', fontSize: 14, lineHeight: 1.7,
    maxWidth: 230, fontFamily: "'Noto Sans KR',sans-serif",
    whiteSpace: 'pre-wrap',
  },

  inputRow: {
    display: 'flex', alignItems: 'flex-end', gap: 8,
    padding: '12px 16px 20px',
    borderTop: '1px solid rgba(196,168,130,0.1)',
  },
  textarea: {
    flex: 1, resize: 'none', overflowY: 'auto', maxHeight: 100,
    background: 'rgba(255,248,240,0.06)',
    border: '1px solid rgba(196,168,130,0.2)',
    borderRadius: 14, padding: '10px 14px',
    color: '#f0e0cc', fontSize: 14,
    fontFamily: "'Noto Sans KR',sans-serif",
    outline: 'none', lineHeight: 1.6,
  },
  sendBtn: {
    width: 40, height: 40, borderRadius: '50%', flexShrink: 0,
    background: 'linear-gradient(135deg,#8b6340,#c4a882)',
    border: 'none', cursor: 'pointer', color: '#fff',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
}
