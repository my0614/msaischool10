import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, MicOff, Download, RefreshCw, X } from 'lucide-react'
import html2canvas from 'html2canvas'
import Card from './Card'
import ScheduleSection from './ScheduleSection'
import KakaoCallback from './KakaoCallback'
import CardViewer from './CardViewer'
import Chatbot from './Chatbot'
import './index.css'

const API = `http://${window.location.hostname}:8000`

export default function App() {
  // 카카오 OAuth 콜백 페이지
  if (window.location.pathname === '/kakao/callback') {
    return <KakaoCallback />
  }

  // 타임캡슐 카드 뷰어 (/card/:id)
  const cardMatch = window.location.pathname.match(/^\/card\/(.+)$/)
  if (cardMatch) {
    return <CardViewer cardId={cardMatch[1]} />
  }
  const [step, setStep] = useState('idle')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [showCard, setShowCard] = useState(false)

  const mediaRecorder = useRef(null)
  const audioChunks = useRef([])
  const audioBlob = useRef(null)
  const cardRef = useRef(null)

  async function startRecording() {
    setError(null)
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.current = new MediaRecorder(stream)
    audioChunks.current = []
    mediaRecorder.current.ondataavailable = e => audioChunks.current.push(e.data)
    mediaRecorder.current.start()
    setStep('recording')
  }

  function stopRecording() {
    return new Promise(resolve => {
      mediaRecorder.current.onstop = () => {
        audioBlob.current = new Blob(audioChunks.current, { type: 'audio/wav' })
        mediaRecorder.current.stream.getTracks().forEach(t => t.stop())
        resolve()
      }
      mediaRecorder.current.stop()
    })
  }

  async function handleSubmit() {
    await stopRecording()
    setStep('processing')
    try {
      const form = new FormData()
      form.append('audio', audioBlob.current, 'recording.wav')
      const res = await fetch(`${API}/api/process`, { method: 'POST', body: form })
      const data = await res.json()
      if (data.error) { setError(data.error); setStep('idle'); return }
      setResult(data)
      setStep('done')
      if (data.tts_b64) playAudio(data.tts_b64)
    } catch {
      setError('서버 연결에 실패했습니다.')
      setStep('idle')
    }
  }

  function playAudio(b64) {
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0))
    const blob = new Blob([bytes], { type: 'audio/wav' })
    new Audio(URL.createObjectURL(blob)).play()
  }

  async function downloadCard() {
    if (!cardRef.current) return
    const canvas = await html2canvas(cardRef.current, { scale: 2, useCORS: true, backgroundColor: null })
    const a = document.createElement('a')
    a.href = canvas.toDataURL('image/png')
    a.download = `dear-me-${result.date}.png`
    a.click()
  }

  function reset() {
    setStep('idle'); setResult(null); setError(null); setShowCard(false)
    audioBlob.current = null
  }

  return (
    <div style={s.page}>
      <div style={s.glow1} /><div style={s.glow2} />

      <div style={s.wrap}>
        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: -24 }}
          animate={{ opacity: 1, y: 0 }}
          style={s.header}
        >
          <span style={s.badge}>✦ Time Capsule Letter ✦</span>
          <h1 style={s.title}>💌 Dear Me,</h1>
          <p style={s.sub}>오늘의 나를 기록하고, 미래의 나에게 편지를 보내세요</p>
        </motion.header>

        <AnimatePresence mode="wait">

          {/* IDLE */}
          {step === 'idle' && (
            <motion.div key="idle"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              style={s.card}
            >
              <p style={s.cardDesc}>마이크 버튼을 눌러 오늘 하루를 말해주세요</p>
              <motion.button
                whileHover={{ scale: 1.06, boxShadow: '0 12px 48px rgba(196,168,130,0.45)' }}
                whileTap={{ scale: 0.94 }}
                onClick={startRecording}
                style={s.micBtn}
              >
                <Mic size={38} />
              </motion.button>
              <p style={s.hint}>버튼을 누르면 녹음이 시작됩니다</p>
              {error && <p style={s.err}>{error}</p>}
            </motion.div>
          )}

          {/* RECORDING */}
          {step === 'recording' && (
            <motion.div key="rec"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              style={s.card}
            >
              <p style={{ ...s.cardDesc, color: '#e87878' }}>🔴 녹음 중 — 말씀해주세요</p>
              <div style={{ position: 'relative', width: 110, height: 110, margin: '0 auto 28px' }}>
                {[0, 1, 2].map(i => (
                  <motion.div key={i}
                    animate={{ scale: [1, 1.6 + i * 0.3], opacity: [0.5, 0] }}
                    transition={{ duration: 1.6, repeat: Infinity, delay: i * 0.5, ease: 'easeOut' }}
                    style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '2px solid #e87878' }}
                  />
                ))}
                <motion.button
                  animate={{ scale: [1, 1.04, 1] }}
                  transition={{ duration: 1.2, repeat: Infinity }}
                  whileTap={{ scale: 0.94 }}
                  onClick={handleSubmit}
                  style={{ ...s.micBtn, background: 'linear-gradient(135deg,#b03030,#e05050)', position: 'relative', zIndex: 1, margin: 0 }}
                >
                  <MicOff size={38} />
                </motion.button>
              </div>
              <p style={s.hint}>정지 버튼을 누르면 편지가 만들어집니다</p>
            </motion.div>
          )}

          {/* PROCESSING */}
          {step === 'processing' && (
            <motion.div key="proc"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{ ...s.card, padding: '60px 36px' }}
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                style={{ marginBottom: 28 }}
              >
                <RefreshCw size={44} color="#c4a882" />
              </motion.div>
              <p style={{ ...s.cardDesc, marginBottom: 28 }}>편지를 작성하고 있어요...</p>
              {['🎤 음성 인식 중', '✍️ 편지 작성 중', '🔊 낭독 준비 중', '📱 QR 카드 생성 중'].map((t, i) => (
                <motion.p key={i}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.45 }}
                  style={{ color: '#8a7065', fontSize: 14, marginBottom: 6 }}
                >{t}</motion.p>
              ))}
            </motion.div>
          )}

          {/* DONE */}
          {step === 'done' && result && (
            <motion.div key="done"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{ width: '100%' }}
            >
              {/* 감정 & 키워드 */}
              <motion.div style={s.card}
                initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
              >
                <p style={s.label}>오늘의 감정</p>
                <div style={s.row}>
                  {result.emotions.map((e, i) => (
                    <motion.span key={i}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.2 + i * 0.1 }}
                      style={s.emoTag}
                    >{e}</motion.span>
                  ))}
                </div>
                <div style={{ ...s.row, marginTop: 10 }}>
                  {result.keywords.map((k, i) => <span key={i} style={s.kwTag}>#{k}</span>)}
                </div>
                <p style={{ color: '#5a4a42', fontSize: 13, marginTop: 14 }}>📝 {result.stt_text}</p>
              </motion.div>

              {/* 편지 */}
              <motion.div style={{ ...s.card, textAlign: 'left', marginTop: 16 }}
                initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
              >
                <p style={s.label}>💌 미래의 나에게</p>
                <p style={{ color: '#5a4a42', fontSize: 12, marginBottom: 20 }}>📅 {result.date}</p>
                <div style={s.letterBox}>
                  {result.letter.split('\n').map((line, i) => (
                    <p key={i} style={{ marginBottom: line === '' ? 14 : 2 }}>{line}</p>
                  ))}
                </div>
              </motion.div>

              {/* QR 코드만 */}
              <motion.div style={{ ...s.card, marginTop: 16, textAlign: 'center' }}
                initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
              >
                <p style={s.label}>📱 타임캡슐 카드</p>
                <p style={{ color: '#5a4a42', fontSize: 14, marginBottom: 24 }}>QR을 눌러 카드를 확인하세요</p>
                <motion.img
                  src={`data:image/png;base64,${result.qr_b64}`}
                  alt="QR"
                  whileHover={{ scale: 1.06, boxShadow: '0 8px 40px rgba(196,168,130,0.3)' }}
                  whileTap={{ scale: 0.96 }}
                  onClick={() => setShowCard(true)}
                  style={s.qrClickable}
                />
                <p style={{ color: '#4a3a32', fontSize: 12, marginTop: 16 }}>클릭하면 카드가 열립니다</p>
              </motion.div>

              {/* 카카오 예약 발송 */}
              <ScheduleSection result={result} />

              <div style={{ textAlign: 'center', marginTop: 20 }}>
                <motion.button
                  whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}
                  onClick={reset} style={s.resetBtn}
                >
                  <RefreshCw size={15} style={{ marginRight: 6 }} /> 다시 기록하기
                </motion.button>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>

      {/* 카드 모달 */}
      <AnimatePresence>
        {showCard && result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowCard(false)}
            style={s.overlay}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.88, y: 40 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.88, y: 40 }}
              transition={{ type: 'spring', damping: 24, stiffness: 300 }}
              onClick={e => e.stopPropagation()}
              style={s.modal}
            >
              {/* 닫기 버튼 */}
              <button onClick={() => setShowCard(false)} style={s.closeBtn}>
                <X size={20} />
              </button>

              {/* 카드 */}
              <Card ref={cardRef} result={result} />

              {/* 다운로드 버튼 */}
              <motion.button
                whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                onClick={downloadCard}
                style={{ ...s.dlBtn, marginTop: 20 }}
              >
                <Download size={15} style={{ marginRight: 6 }} /> 카드 이미지 저장
              </motion.button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <Chatbot />
    </div>
  )
}

const s = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(160deg,#1a0f0a 0%,#2d1810 60%,#1a0f0a 100%)',
    display: 'flex', justifyContent: 'center',
    padding: '48px 20px 80px', position: 'relative', overflow: 'hidden',
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
    width: '100%', maxWidth: 820,
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    position: 'relative', zIndex: 1,
  },
  header: { textAlign: 'center', marginBottom: 40 },
  badge: { display: 'inline-block', fontSize: 11, letterSpacing: 3, color: '#8a7065', textTransform: 'uppercase', marginBottom: 18 },
  title: { fontFamily: "'Noto Serif KR',serif", fontSize: 54, fontWeight: 300, color: '#f5ebe0', letterSpacing: -1, marginBottom: 14, lineHeight: 1.1 },
  sub: { color: '#6a5a52', fontSize: 16, lineHeight: 1.7 },
  card: {
    width: '100%',
    background: 'rgba(255,248,240,0.035)',
    border: '1px solid rgba(196,168,130,0.12)',
    borderRadius: 24, padding: '40px 40px',
    backdropFilter: 'blur(12px)',
    textAlign: 'center',
  },
  cardDesc: { fontFamily: "'Noto Serif KR',serif", color: '#c4a882', fontSize: 18, marginBottom: 36 },
  micBtn: {
    width: 110, height: 110, borderRadius: '50%', border: 'none',
    background: 'linear-gradient(135deg,#8b6340,#c4a882)',
    color: '#fff', cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    margin: '0 auto 28px',
    boxShadow: '0 8px 36px rgba(196,168,130,0.28)',
  },
  hint: { color: '#4a3a32', fontSize: 14 },
  err: { color: '#e07070', marginTop: 16, fontSize: 14 },
  label: { color: '#c4a882', fontSize: 11, letterSpacing: 2.5, textTransform: 'uppercase', marginBottom: 18, fontWeight: 500 },
  row: { display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center' },
  emoTag: { background: 'rgba(196,168,130,0.12)', border: '1px solid rgba(196,168,130,0.25)', borderRadius: 20, padding: '6px 18px', fontSize: 15, color: '#f0e0cc' },
  kwTag: { color: '#6a5a52', fontSize: 14 },
  letterBox: { fontFamily: "'Noto Serif KR',serif", fontSize: 16, lineHeight: 2.1, color: '#e8d5c0', background: 'rgba(0,0,0,0.15)', borderRadius: 16, padding: '24px 28px' },
  qrClickable: {
    width: 200, height: 200, borderRadius: 16, cursor: 'pointer',
    border: '2px solid rgba(196,168,130,0.25)',
    boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
    display: 'block', margin: '0 auto',
    transition: 'box-shadow 0.2s',
  },
  resetBtn: {
    display: 'inline-flex', alignItems: 'center',
    background: 'transparent', border: '1px solid rgba(196,168,130,0.25)',
    borderRadius: 12, padding: '10px 28px',
    color: '#8a7065', fontSize: 14, cursor: 'pointer', fontFamily: "'Noto Sans KR',sans-serif",
  },

  // 모달
  overlay: {
    position: 'fixed', inset: 0, zIndex: 100,
    background: 'rgba(10,5,3,0.85)',
    backdropFilter: 'blur(8px)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    padding: 24,
  },
  modal: {
    position: 'relative',
    width: '100%', maxWidth: 600,
    maxHeight: '92vh', overflowY: 'auto',
    background: 'transparent',
    borderRadius: 24,
    padding: '40px 20px 20px',
    boxShadow: '0 40px 100px rgba(0,0,0,0.7)',
    display: 'flex', flexDirection: 'column', alignItems: 'center',
  },
  closeBtn: {
    position: 'absolute', top: 8, right: 8,
    background: 'rgba(44,26,14,0.8)', border: '1px solid rgba(196,168,130,0.3)',
    borderRadius: '50%', width: 36, height: 36,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    cursor: 'pointer', color: '#c4a882', zIndex: 10,
  },
  dlBtn: {
    display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%',
    background: 'linear-gradient(135deg,#8b6340,#c4a882)',
    border: 'none', borderRadius: 14, padding: '13px',
    color: '#fff', fontSize: 15, cursor: 'pointer', fontFamily: "'Noto Sans KR',sans-serif",
    boxShadow: '0 4px 20px rgba(196,168,130,0.2)',
  },
}
