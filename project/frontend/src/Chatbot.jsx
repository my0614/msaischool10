import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, MessageCircle } from 'lucide-react'

const API = `http://${window.location.hostname}:8000`

const GREETING = '안녕, 나 비밀 친구야.\n오늘 하루 어땠어?'

function BotAvatar() {
  return (
    <div style={{
      width: 30, height: 30, borderRadius: '50%', flexShrink: 0,
      background: 'linear-gradient(135deg, #3d2010, #7a5230)',
      border: '1px solid rgba(196,168,130,0.35)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      alignSelf: 'flex-end', marginBottom: 2, marginRight: 8,
    }}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#c4a882" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
      </svg>
    </div>
  )
}

function TypingDots() {
  return (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center', padding: '4px 2px' }}>
      {[0, 1, 2].map(i => (
        <motion.div
          key={i}
          style={{ width: 6, height: 6, borderRadius: '50%', background: '#8a7060' }}
          animate={{ y: [0, -5, 0], opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.18, ease: 'easeInOut' }}
        />
      ))}
    </div>
  )
}

export default function Chatbot() {
  const [open, setOpen]         = useState(false)
  const [messages, setMessages] = useState([{ role: 'assistant', content: GREETING }])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const bottomRef               = useRef(null)
  const inputRef                = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 320)
  }, [open])

  async function send() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')

    const next = [...messages, { role: 'user', content: text }]
    setMessages(next)
    setLoading(true)

    try {
      const res = await fetch(`${API}/api/chat`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ messages: next }),
      }).then(r => r.json())

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.reply || res.error || '...',
      }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '잠깐 연결이 끊겼어. 다시 말해줘.' }])
    } finally {
      setLoading(false)
    }
  }

  function onKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <>
      {/* 플로팅 버튼 — 패널 닫혀있을 때만 표시 */}
      <AnimatePresence>
        {!open && (
          <motion.button
            initial={{ scale: 0.7, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.7, opacity: 0 }}
            transition={{ duration: 0.18 }}
            whileHover={{ scale: 1.08, boxShadow: '0 12px 40px rgba(196,168,130,0.25)' }}
            whileTap={{ scale: 0.94 }}
            onClick={() => setOpen(true)}
            style={s.fab}
            title="비밀 친구와 대화하기"
          >
            <MessageCircle size={22} strokeWidth={1.8} />
            <motion.div
              style={s.fabBadge}
              initial={{ scale: 0 }} animate={{ scale: 1 }}
              transition={{ delay: 0.5, type: 'spring' }}
            />
          </motion.button>
        )}
      </AnimatePresence>

      {/* 사이드 패널 */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            style={s.panel}
          >
            {/* 헤더 */}
            <div style={s.header}>
              <div style={s.headerGlow} />
              <div style={s.headerInner}>
                <div style={s.headerAvatarWrap}>
                  <div style={s.headerAvatar}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#c4a882" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                    </svg>
                  </div>
                  <div style={s.onlineDot} />
                </div>
                <div>
                  <p style={s.headerName}>비밀 친구</p>
                  <p style={s.headerSub}>언제든 털어놔</p>
                </div>
              </div>
              <button onClick={() => setOpen(false)} style={s.closeBtn}>
                <X size={16} strokeWidth={2} />
              </button>
            </div>

            {/* 날짜 구분선 */}
            <div style={s.dateLine}>
              <span style={s.dateText}>오늘</span>
            </div>

            {/* 메시지 영역 */}
            <div style={s.messages}>
              {messages.map((m, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.22 }}
                  style={{
                    display: 'flex',
                    justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
                    alignItems: 'flex-end',
                    marginBottom: 10,
                  }}
                >
                  {m.role === 'assistant' && <BotAvatar />}
                  <div style={m.role === 'user' ? s.userBubble : s.botBubble}>
                    {m.content}
                  </div>
                </motion.div>
              ))}

              {loading && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  style={{ display: 'flex', alignItems: 'flex-end', marginBottom: 10 }}
                >
                  <BotAvatar />
                  <div style={{ ...s.botBubble, padding: '10px 16px' }}>
                    <TypingDots />
                  </div>
                </motion.div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* 입력 영역 */}
            <div style={s.inputWrap}>
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
                  whileHover={{ scale: 1.08 }}
                  whileTap={{ scale: 0.92 }}
                  onClick={send}
                  disabled={!input.trim() || loading}
                  style={{
                    ...s.sendBtn,
                    background: input.trim() && !loading
                      ? 'linear-gradient(135deg,#7a5230,#c4a882)'
                      : 'rgba(196,168,130,0.1)',
                  }}
                >
                  <Send size={15} strokeWidth={2} style={{ transform: 'translateX(1px)' }} />
                </motion.button>
              </div>
              <p style={s.inputHint}>Enter로 전송 · Shift+Enter 줄바꿈</p>
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
    width: 52, height: 52, borderRadius: '50%',
    background: 'linear-gradient(135deg, #3d2010 0%, #7a5230 100%)',
    border: '1px solid rgba(196,168,130,0.3)',
    boxShadow: '0 6px 28px rgba(0,0,0,0.45)',
    cursor: 'pointer', color: '#d4b896',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    outline: 'none', position: 'fixed',
  },
  fabBadge: {
    position: 'absolute', top: 10, right: 10,
    width: 8, height: 8, borderRadius: '50%',
    background: '#c4a882',
    boxShadow: '0 0 0 2px #2d1810',
  },

  panel: {
    position: 'fixed', right: 0, top: 0, bottom: 0, zIndex: 150,
    width: 360,
    background: '#16100a',
    borderLeft: '1px solid rgba(196,168,130,0.12)',
    boxShadow: '-20px 0 60px rgba(0,0,0,0.6)',
    display: 'flex', flexDirection: 'column',
    fontFamily: "'Noto Sans KR', sans-serif",
  },

  header: {
    position: 'relative', overflow: 'hidden',
    padding: '18px 18px 16px',
    borderBottom: '1px solid rgba(196,168,130,0.1)',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  },
  headerGlow: {
    position: 'absolute', top: -60, left: -60, width: 180, height: 180,
    borderRadius: '50%', pointerEvents: 'none',
    background: 'radial-gradient(circle, rgba(196,168,130,0.07) 0%, transparent 70%)',
  },
  headerInner: { display: 'flex', alignItems: 'center', gap: 12, position: 'relative', zIndex: 1 },
  headerAvatarWrap: { position: 'relative' },
  headerAvatar: {
    width: 42, height: 42, borderRadius: '50%',
    background: 'linear-gradient(135deg, #2a1508, #5a3520)',
    border: '1px solid rgba(196,168,130,0.25)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  onlineDot: {
    position: 'absolute', bottom: 1, right: 1,
    width: 10, height: 10, borderRadius: '50%',
    background: '#7db87d',
    border: '2px solid #16100a',
  },
  headerName: { color: '#e8d5c0', fontSize: 14, fontWeight: 600, margin: 0, letterSpacing: 0.3 },
  headerSub:  { color: '#5a4a42', fontSize: 11, margin: '3px 0 0', letterSpacing: 0.2 },
  closeBtn: {
    background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(196,168,130,0.1)',
    borderRadius: 8, width: 30, height: 30,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    cursor: 'pointer', color: '#5a4a42', flexShrink: 0,
    position: 'relative', zIndex: 1,
  },

  dateLine: {
    display: 'flex', alignItems: 'center', gap: 10,
    padding: '14px 20px 4px',
  },
  dateText: { color: '#3a2a22', fontSize: 11, letterSpacing: 1, textTransform: 'uppercase' },

  messages: {
    flex: 1, overflowY: 'auto', padding: '12px 16px 4px',
    display: 'flex', flexDirection: 'column',
    scrollbarWidth: 'thin',
    scrollbarColor: 'rgba(196,168,130,0.1) transparent',
  },

  botBubble: {
    background: 'rgba(196,168,130,0.07)',
    border: '1px solid rgba(196,168,130,0.13)',
    borderRadius: '16px 16px 16px 4px',
    padding: '10px 14px',
    color: '#d4c0ac', fontSize: 13.5, lineHeight: 1.75,
    maxWidth: 220, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
  },
  userBubble: {
    background: 'linear-gradient(135deg, #5a3018, #7a4c28)',
    border: '1px solid rgba(196,168,130,0.15)',
    borderRadius: '16px 16px 4px 16px',
    padding: '10px 14px',
    color: '#f5e8d8', fontSize: 13.5, lineHeight: 1.75,
    maxWidth: 220, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
  },

  inputWrap: {
    borderTop: '1px solid rgba(196,168,130,0.08)',
    padding: '12px 14px 16px',
    background: 'rgba(0,0,0,0.15)',
  },
  inputRow: {
    display: 'flex', alignItems: 'flex-end', gap: 8,
  },
  textarea: {
    flex: 1, resize: 'none', overflowY: 'auto', maxHeight: 90,
    background: 'rgba(255,248,240,0.05)',
    border: '1px solid rgba(196,168,130,0.18)',
    borderRadius: 12, padding: '9px 13px',
    color: '#e8d5c0', fontSize: 13.5,
    fontFamily: "'Noto Sans KR', sans-serif",
    outline: 'none', lineHeight: 1.6,
    transition: 'border-color 0.2s',
  },
  sendBtn: {
    width: 38, height: 38, borderRadius: 12, flexShrink: 0,
    border: 'none', cursor: 'pointer', color: '#e8d5c0',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    transition: 'background 0.2s',
  },
  inputHint: {
    color: '#2e2018', fontSize: 10, margin: '7px 0 0', letterSpacing: 0.3,
    textAlign: 'center',
  },
}
