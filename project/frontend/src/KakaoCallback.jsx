import { useEffect, useState, useRef } from 'react'

const API = `http://${window.location.hostname}:8000`

export default function KakaoCallback() {
  const [status, setStatus] = useState('processing')
  const [errorMsg, setErrorMsg] = useState('')
  const called = useRef(false)  // StrictMode 이중 실행 방지

  useEffect(() => {
    if (called.current) return
    called.current = true

    const params = new URLSearchParams(window.location.search)
    const code  = params.get('code')
    const state = params.get('state')
    const error = params.get('error')

    if (error) {
      setErrorMsg(error)
      setStatus('error')
      return
    }

    if (!code || !state) {
      setErrorMsg('code 또는 state 파라미터가 없습니다.')
      setStatus('error')
      return
    }

    fetch(`${API}/api/kakao/exchange?code=${code}&state=${state}`)
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          setStatus('done')
          window.opener?.postMessage('kakao-auth-complete', '*')
          setTimeout(() => window.close(), 1200)
        } else {
          setErrorMsg(data.error || '알 수 없는 오류')
          setStatus('error')
        }
      })
      .catch(() => {
        setErrorMsg('백엔드 서버에 연결할 수 없습니다.')
        setStatus('error')
      })
  }, [])

  return (
    <div style={s.page}>
      {status === 'processing' && (
        <>
          <div style={s.spinner} />
          <p style={s.text}>카카오 로그인 처리 중...</p>
        </>
      )}
      {status === 'done' && (
        <>
          <div style={s.emoji}>✅</div>
          <h2 style={s.title}>로그인 완료!</h2>
          <p style={s.text}>이 창은 자동으로 닫힙니다</p>
        </>
      )}
      {status === 'error' && (
        <>
          <div style={s.emoji}>❌</div>
          <h2 style={s.title}>로그인 실패</h2>
          <p style={{ ...s.text, color: '#e07070' }}>{errorMsg}</p>
        </>
      )}
    </div>
  )
}

const s = {
  page: {
    minHeight: '100vh',
    background: '#1a0f0a',
    display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center',
    fontFamily: "'Apple SD Gothic Neo', sans-serif",
    gap: 16,
  },
  emoji: { fontSize: 52 },
  title: { color: '#f5ebe0', fontWeight: 400, margin: 0 },
  text:  { color: '#c4a882', fontSize: 15, margin: 0 },
  spinner: {
    width: 40, height: 40,
    border: '3px solid rgba(196,168,130,0.2)',
    borderTop: '3px solid #c4a882',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
}
