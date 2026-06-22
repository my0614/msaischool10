import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'

const API = `http://${window.location.hostname}:8000`

export default function LoginPage({ onLogin }) {
  const [status, setStatus] = useState('idle') // idle | waiting | done
  const [error, setError]   = useState(null)
  const pollRef = useRef(null)

  useEffect(() => () => clearInterval(pollRef.current), [])

  async function handleKakaoLogin() {
    setError(null)
    setStatus('waiting')

    const stateKey = crypto.randomUUID()

    try {
      const { url } = await fetch(`${API}/api/kakao/auth-url?state=${stateKey}`).then(r => r.json())
      const popup = window.open(url, 'kakao-login', 'width=520,height=720,left=200,top=100')

      const finishLogin = async () => {
        const { nickname } = await fetch(`${API}/api/me?state=${stateKey}`).then(r => r.json()).catch(() => ({}))
        localStorage.setItem('kakao_state', stateKey)
        if (nickname) localStorage.setItem('kakao_nickname', nickname)
        setStatus('done')
        setTimeout(() => onLogin(stateKey, nickname || ''), 800)
      }

      const onMsg = (e) => {
        if (e.data !== 'kakao-auth-complete') return
        clearInterval(pollRef.current)
        window.removeEventListener('message', onMsg)
        popup?.close()
        finishLogin()
      }
      window.addEventListener('message', onMsg)

      pollRef.current = setInterval(async () => {
        const { authenticated } = await fetch(`${API}/api/kakao/status/${stateKey}`).then(r => r.json())
        if (!authenticated) return
        clearInterval(pollRef.current)
        window.removeEventListener('message', onMsg)
        popup?.close()
        finishLogin()
      }, 2000)
    } catch {
      setStatus('idle')
      setError('서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해주세요.')
    }
  }

  return (
    <div style={s.page}>
      <div style={s.glow1} />
      <div style={s.glow2} />

      <motion.div
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={s.box}
      >
        <motion.div
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          style={s.emoji}
        >
          💌
        </motion.div>

        <span style={s.badge}>✦ Time Capsule Letter ✦</span>
        <h1 style={s.title}>Dear Me,</h1>
        <p style={s.sub}>
          오늘의 나를 기록하고<br />
          미래의 나에게 편지를 보내세요
        </p>

        <div style={s.divider} />

        {status === 'done' ? (
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            style={s.success}
          >
            ✅ 로그인 완료! 잠시 후 이동합니다...
          </motion.p>
        ) : (
          <motion.button
            whileHover={{ scale: 1.03, boxShadow: '0 8px 36px rgba(254,229,0,0.35)' }}
            whileTap={{ scale: 0.97 }}
            onClick={handleKakaoLogin}
            disabled={status === 'waiting'}
            style={{ ...s.kakaoBtn, opacity: status === 'waiting' ? 0.75 : 1 }}
          >
            <span style={{ fontSize: 22 }}>💬</span>
            {status === 'waiting' ? '로그인 창을 확인해주세요...' : '카카오로 시작하기'}
          </motion.button>
        )}

        {error && (
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={s.err}>
            {error}
          </motion.p>
        )}

        <p style={s.hint}>
          카카오 계정으로 간편하게 시작하세요<br />
          <span style={{ color: '#4a3a32', fontSize: 11 }}>별도 회원가입 없이 이용 가능합니다</span>
        </p>
      </motion.div>
    </div>
  )
}

const s = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(160deg,#1a0f0a 0%,#2d1810 60%,#1a0f0a 100%)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    position: 'relative', overflow: 'hidden', padding: 24,
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
  box: {
    width: '100%', maxWidth: 420,
    background: 'rgba(255,248,240,0.035)',
    border: '1px solid rgba(196,168,130,0.15)',
    borderRadius: 28, padding: '52px 44px',
    backdropFilter: 'blur(12px)',
    textAlign: 'center', position: 'relative', zIndex: 1,
  },
  emoji:  { fontSize: 52, marginBottom: 20 },
  badge:  { display: 'inline-block', fontSize: 10, letterSpacing: 3, color: '#6a5a52', textTransform: 'uppercase', marginBottom: 16 },
  title:  { fontFamily: "'Noto Serif KR',serif", fontSize: 48, fontWeight: 300, color: '#f5ebe0', letterSpacing: -1, margin: '0 0 12px' },
  sub:    { color: '#6a5a52', fontSize: 15, lineHeight: 1.9 },
  divider: { width: 40, height: 1, background: 'rgba(196,168,130,0.2)', margin: '32px auto' },
  kakaoBtn: {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 10,
    width: '100%', background: '#FEE500', border: 'none', borderRadius: 16,
    padding: '15px 24px', fontSize: 16, fontWeight: 700, color: '#1a1a1a',
    cursor: 'pointer', fontFamily: "'Noto Sans KR',sans-serif",
    boxShadow: '0 4px 24px rgba(254,229,0,0.2)',
  },
  success: { color: '#c4a882', fontSize: 15, padding: '14px 0' },
  err:     { color: '#e07070', fontSize: 13, marginTop: 14 },
  hint:    { color: '#5a4a42', fontSize: 12, marginTop: 28, lineHeight: 1.9 },
}
