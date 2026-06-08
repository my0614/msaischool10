import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, Check } from 'lucide-react'

const API = 'http://localhost:8000'

const OPTIONS = [
  { label: '한 달 후',  emoji: '🌙', days: 30 },
  { label: '100일 후', emoji: '💯', days: 100 },
  { label: '새해 첫날', emoji: '🎆', special: 'newyear' },
  { label: '1년 후',   emoji: '🌟', days: 365 },
]

function getScheduledDate(opt) {
  const now = new Date()
  if (opt.special === 'newyear') {
    return new Date(now.getFullYear() + 1, 0, 1, 9, 0, 0)
  }
  const d = new Date(now)
  d.setDate(d.getDate() + opt.days)
  d.setHours(9, 0, 0, 0)
  return d
}

function formatDate(d) {
  return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
}

export default function ScheduleSection({ result }) {
  const [selected, setSelected]     = useState(null)
  const [authStep, setAuthStep]     = useState('idle')  // idle | waiting | done
  const [stateKey, setStateKey]     = useState(null)
  const [done, setDone]             = useState(false)
  const [error, setError]           = useState(null)
  const pollRef                     = useRef(null)

  useEffect(() => () => clearInterval(pollRef.current), [])

  async function handleKakaoLogin() {
    setError(null)
    const key = crypto.randomUUID()
    setStateKey(key)
    setAuthStep('waiting')

    const { url } = await fetch(`${API}/api/kakao/auth-url?state=${key}`).then(r => r.json())
    const popup = window.open(url, 'kakao-auth', 'width=520,height=720,left=200,top=100')

    // postMessage 수신
    const onMsg = (e) => {
      if (e.data === 'kakao-auth-complete') {
        setAuthStep('done')
        clearInterval(pollRef.current)
        window.removeEventListener('message', onMsg)
        popup?.close()
      }
    }
    window.addEventListener('message', onMsg)

    // 폴링 fallback (팝업 차단 대비)
    pollRef.current = setInterval(async () => {
      const { authenticated } = await fetch(`${API}/api/kakao/status/${key}`).then(r => r.json())
      if (authenticated) {
        setAuthStep('done')
        clearInterval(pollRef.current)
        window.removeEventListener('message', onMsg)
      }
    }, 2000)
  }

  async function handleSchedule() {
    if (!selected || !stateKey) return
    setError(null)

    const opt  = OPTIONS.find(o => o.label === selected)
    const date = getScheduledDate(opt)

    const res = await fetch(`${API}/api/schedule`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        state:          stateKey,
        letter:         result.letter,
        emotions:       result.emotions,
        keywords:       result.keywords,
        date_scheduled: date.toISOString(),
      }),
    }).then(r => r.json())

    if (res.error) { setError(res.error); return }
    setDone(true)
  }

  // ── 완료 화면 ──────────────────────────────────────────────
  if (done) {
    const opt  = OPTIONS.find(o => o.label === selected)
    const date = getScheduledDate(opt)
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        style={s.doneBox}
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', delay: 0.1 }}
          style={s.doneIcon}
        >✅</motion.div>
        <p style={s.doneTitle}>예약 완료!</p>
        <p style={s.doneDesc}>
          <strong>{formatDate(date)}</strong><br />
          오전 9시에 카카오톡으로<br />편지가 도착할 거예요 💌
        </p>
      </motion.div>
    )
  }

  // ── 메인 UI ────────────────────────────────────────────────
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      style={s.wrap}
    >
      {/* 헤더 */}
      <div style={s.header}>
        <p style={s.label}>📬 나중에 카카오톡으로 받기</p>
        <p style={s.desc}>편지를 미래의 날짜에 카톡으로 받아보세요</p>
      </div>

      {/* 날짜 선택 */}
      <div style={s.grid}>
        {OPTIONS.map(opt => {
          const active = selected === opt.label
          const date   = getScheduledDate(opt)
          return (
            <motion.button key={opt.label}
              whileHover={{ scale: 1.04, y: -2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setSelected(opt.label)}
              style={{ ...s.optBtn, ...(active ? s.optActive : {}) }}
            >
              <span style={s.optEmoji}>{opt.emoji}</span>
              <span style={s.optLabel}>{opt.label}</span>
              <span style={s.optDate}>{formatDate(date)}</span>
              {active && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  style={s.checkBadge}
                >
                  <Check size={10} />
                </motion.div>
              )}
            </motion.button>
          )
        })}
      </div>

      {/* 카카오 로그인 / 예약 버튼 */}
      <AnimatePresence mode="wait">
        {selected && (
          <motion.div key="actions"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            style={s.actions}
          >
            {authStep !== 'done' ? (
              <motion.button
                whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                onClick={handleKakaoLogin}
                disabled={authStep === 'waiting'}
                style={s.kakaoBtn}
              >
                <span style={s.kakaoIcon}>💬</span>
                {authStep === 'waiting' ? '로그인 창을 확인해주세요...' : '카카오로 로그인'}
              </motion.button>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{ textAlign: 'center' }}
              >
                <p style={s.authDone}>✓ 카카오 로그인 완료</p>
                <motion.button
                  whileHover={{ scale: 1.03, boxShadow: '0 8px 30px rgba(196,168,130,0.35)' }}
                  whileTap={{ scale: 0.97 }}
                  onClick={handleSchedule}
                  style={s.scheduleBtn}
                >
                  <Clock size={16} style={{ marginRight: 8 }} />
                  {selected}에 카톡으로 받기
                </motion.button>
              </motion.div>
            )}
            {error && <p style={s.err}>{error}</p>}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

const s = {
  wrap: {
    width: '100%',
    background: 'rgba(255,248,240,0.035)',
    border: '1px solid rgba(196,168,130,0.12)',
    borderRadius: 24, padding: '36px 40px',
    marginTop: 16,
  },
  header: { textAlign: 'center', marginBottom: 28 },
  label: { color: '#c4a882', fontSize: 11, letterSpacing: 2.5, textTransform: 'uppercase', fontWeight: 500, marginBottom: 10 },
  desc: { color: '#6a5a52', fontSize: 14 },

  grid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 8 },

  optBtn: {
    position: 'relative',
    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
    padding: '18px 10px',
    background: 'rgba(255,248,240,0.04)',
    border: '1px solid rgba(196,168,130,0.15)',
    borderRadius: 16, cursor: 'pointer',
    transition: 'all 0.2s',
  },
  optActive: {
    background: 'rgba(196,168,130,0.12)',
    border: '1px solid rgba(196,168,130,0.5)',
    boxShadow: '0 4px 20px rgba(196,168,130,0.15)',
  },
  optEmoji: { fontSize: 26 },
  optLabel: { color: '#f0e0cc', fontSize: 13, fontWeight: 500, fontFamily: "'Noto Sans KR', sans-serif" },
  optDate:  { color: '#6a5a52', fontSize: 11, fontFamily: "'Noto Sans KR', sans-serif" },
  checkBadge: {
    position: 'absolute', top: 8, right: 8,
    background: '#c4a882', borderRadius: '50%',
    width: 18, height: 18,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    color: '#1a0f0a',
  },

  actions: { marginTop: 24, textAlign: 'center' },

  kakaoBtn: {
    display: 'inline-flex', alignItems: 'center', gap: 10,
    background: '#FEE500', border: 'none', borderRadius: 14,
    padding: '13px 32px', fontSize: 15, fontWeight: 600,
    color: '#1a1a1a', cursor: 'pointer',
    fontFamily: "'Noto Sans KR', sans-serif",
    boxShadow: '0 4px 20px rgba(254,229,0,0.25)',
  },
  kakaoIcon: { fontSize: 20 },

  authDone: { color: '#c4a882', fontSize: 13, marginBottom: 14 },

  scheduleBtn: {
    display: 'inline-flex', alignItems: 'center',
    background: 'linear-gradient(135deg,#8b6340,#c4a882)',
    border: 'none', borderRadius: 14, padding: '13px 32px',
    color: '#fff', fontSize: 15, cursor: 'pointer',
    fontFamily: "'Noto Sans KR', sans-serif",
    boxShadow: '0 4px 20px rgba(196,168,130,0.2)',
  },
  err: { color: '#e07070', fontSize: 13, marginTop: 12 },

  doneBox: {
    width: '100%',
    background: 'rgba(196,168,130,0.06)',
    border: '1px solid rgba(196,168,130,0.2)',
    borderRadius: 24, padding: '40px',
    marginTop: 16, textAlign: 'center',
  },
  doneIcon:  { fontSize: 48, marginBottom: 16 },
  doneTitle: { fontFamily: "'Noto Serif KR', serif", fontSize: 22, color: '#f5ebe0', marginBottom: 12 },
  doneDesc:  { color: '#8a7065', fontSize: 15, lineHeight: 1.8, fontFamily: "'Noto Sans KR', sans-serif" },
}
