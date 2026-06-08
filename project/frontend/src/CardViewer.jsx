import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import Card from './Card'

const API = `http://${window.location.hostname}:8000`

export default function CardViewer({ cardId }) {
  const [result, setResult] = useState(null)
  const [error, setError]   = useState(null)

  useEffect(() => {
    fetch(`${API}/api/card/${cardId}`)
      .then(r => r.json())
      .then(data => {
        if (data.error) { setError(data.error); return }
        setResult({ ...data, qr_b64: null })
      })
      .catch(() => setError('서버에 연결할 수 없습니다.'))
  }, [cardId])

  if (error) return (
    <div style={s.page}>
      <div style={s.box}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>💌</div>
        <p style={{ color: '#e07070', fontSize: 16 }}>{error}</p>
      </div>
    </div>
  )

  if (!result) return (
    <div style={s.page}>
      <div style={s.box}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          style={{ fontSize: 40 }}
        >⏳</motion.div>
        <p style={{ color: '#c4a882', marginTop: 16 }}>카드를 불러오는 중...</p>
      </div>
    </div>
  )

  return (
    <div style={s.page}>
      <div style={s.glow1} /><div style={s.glow2} />
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', damping: 22 }}
        style={s.wrap}
      >
        <p style={s.badge}>✦ Time Capsule Letter ✦</p>
        <Card result={result} />
        <p style={s.hint}>과거의 내가 미래의 나에게 보낸 편지입니다 💌</p>
      </motion.div>
    </div>
  )
}

const s = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(160deg,#1a0f0a 0%,#2d1810 60%,#1a0f0a 100%)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: '40px 20px', position: 'relative', overflow: 'hidden',
  },
  glow1: {
    position: 'fixed', top: -200, right: -200, width: 600, height: 600,
    borderRadius: '50%', pointerEvents: 'none',
    background: 'radial-gradient(circle,rgba(196,168,130,0.09) 0%,transparent 70%)',
  },
  glow2: {
    position: 'fixed', bottom: -200, left: -200, width: 500, height: 500,
    borderRadius: '50%', pointerEvents: 'none',
    background: 'radial-gradient(circle,rgba(160,100,80,0.07) 0%,transparent 70%)',
  },
  wrap: {
    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20,
    position: 'relative', zIndex: 1, width: '100%', maxWidth: 600,
  },
  box: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', minHeight: '60vh', gap: 12,
  },
  badge: { color: '#8a7065', fontSize: 11, letterSpacing: 3, textTransform: 'uppercase' },
  hint:  { color: '#5a4a42', fontSize: 14, fontFamily: "'Noto Sans KR', sans-serif" },
}
