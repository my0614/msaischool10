import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, Check } from 'lucide-react'

const API = `http://${window.location.hostname}:8000`

const DATE_OPTIONS = [
  { label: '지금 바로', emoji: '⚡', immediate: true },
  { label: '한 달 후',  emoji: '🌙', days: 30 },
  { label: '100일 후', emoji: '💯', days: 100 },
  { label: '새해 첫날', emoji: '🎆', special: 'newyear' },
  { label: '1년 후',   emoji: '🌟', days: 365 },
]

const CHANNELS = [
  { id: 'kakao',   label: '카카오톡', emoji: '💬', desc: 'OAuth 로그인 후 나에게 보내기' },
  { id: 'discord', label: '디스코드', emoji: '🎮', desc: '웹훅 URL로 채널에 전송' },
  { id: 'email',   label: '이메일',   emoji: '📧', desc: 'Gmail로 편지 발송' },
]

function getScheduledDate(opt) {
  if (opt.immediate) {
    const d = new Date()
    d.setSeconds(d.getSeconds() + 15)  // 15초 뒤 발송 (flow 완료 버퍼)
    return d
  }
  const now = new Date()
  if (opt.special === 'newyear') return new Date(now.getFullYear() + 1, 0, 1, 9, 0, 0)
  const d = new Date(now)
  d.setDate(d.getDate() + opt.days)
  d.setHours(9, 0, 0, 0)
  return d
}

function formatDate(d) {
  return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
}

export default function ScheduleSection({ result, kakaoStateKey }) {
  const [dateOpt, setDateOpt]               = useState(null)
  const [channel, setChannel]               = useState(null)
  const [authStep, setAuthStep]             = useState(kakaoStateKey ? 'done' : 'idle')
  const [stateKey, setStateKey]             = useState(kakaoStateKey ?? null)
  const [discordWebhook, setDiscordWebhook] = useState('')
  const [targetEmail, setTargetEmail]       = useState('')
  const [done, setDone]                     = useState(false)
  const [error, setError]                   = useState(null)
  const pollRef                             = useRef(null)

  useEffect(() => () => clearInterval(pollRef.current), [])

  function handleChannelSelect(ch) {
    setChannel(ch)
    setAuthStep('idle')
    setStateKey(null)
    setError(null)
  }

  async function handleKakaoLogin() {
    setError(null)
    const key = crypto.randomUUID()
    setStateKey(key)
    setAuthStep('waiting')

    const { url } = await fetch(`${API}/api/kakao/auth-url?state=${key}`).then(r => r.json())
    const popup = window.open(url, 'kakao-auth', 'width=520,height=720,left=200,top=100')

    const onMsg = (e) => {
      if (e.data === 'kakao-auth-complete') {
        setAuthStep('done')
        clearInterval(pollRef.current)
        window.removeEventListener('message', onMsg)
        popup?.close()
      }
    }
    window.addEventListener('message', onMsg)

    pollRef.current = setInterval(async () => {
      const { authenticated } = await fetch(`${API}/api/kakao/status/${key}`).then(r => r.json())
      if (authenticated) {
        setAuthStep('done')
        clearInterval(pollRef.current)
        window.removeEventListener('message', onMsg)
      }
    }, 2000)
  }

  function canSchedule() {
    if (!dateOpt || !channel) return false
    if (channel === 'kakao')   return authStep === 'done'
    if (channel === 'discord') return discordWebhook.startsWith('https://discord.com/api/webhooks/')
    if (channel === 'email')   return targetEmail.includes('@') && targetEmail.includes('.')
    return false
  }

  async function handleSchedule() {
    if (!canSchedule()) return
    setError(null)

    const opt  = DATE_OPTIONS.find(o => o.label === dateOpt)
    const date = getScheduledDate(opt)

    const body = {
      send_method:    channel,
      letter:         result.letter,
      emotions:       result.emotions,
      keywords:       result.keywords,
      date_scheduled: date.toISOString(),
    }
    if (channel === 'kakao')   body.state           = stateKey
    if (channel === 'discord') body.discord_webhook = discordWebhook
    if (channel === 'email')   body.target_email    = targetEmail

    const res = await fetch(`${API}/api/schedule`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body),
    }).then(r => r.json())

    if (res.error) { setError(res.error); return }
    setDone(true)
  }

  // ── 완료 화면
  if (done) {
    const opt  = DATE_OPTIONS.find(o => o.label === dateOpt)
    const date = getScheduledDate(opt)
    const ch   = CHANNELS.find(c => c.id === channel)
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        style={s.doneBox}
      >
        <motion.div
          initial={{ scale: 0 }} animate={{ scale: 1 }}
          transition={{ type: 'spring', delay: 0.1 }}
          style={s.doneIcon}
        >✅</motion.div>
        <p style={s.doneTitle}>예약 완료!</p>
        <p style={s.doneDesc}>
          {opt?.immediate ? (
            <>{ch?.label}으로<br />편지가 바로 발송됩니다 {ch?.emoji}</>
          ) : (
            <><strong>{formatDate(date)}</strong><br />오전 9시에 {ch?.label}으로<br />편지가 도착할 거예요 {ch?.emoji}</>
          )}
        </p>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      style={s.wrap}
    >
      {/* 헤더 */}
      <div style={s.header}>
        <p style={s.label}>📬 미래에 받기</p>
        <p style={s.desc}>편지를 원하는 날짜에 받아보세요</p>
      </div>

      {/* 지금 바로 받기 */}
      {(() => {
        const immOpt = DATE_OPTIONS.find(o => o.immediate)
        const active = dateOpt === immOpt.label
        return (
          <motion.button
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setDateOpt(immOpt.label)}
            style={{ ...s.immediateBtn, ...(active ? s.immediateActive : {}) }}
          >
            <span style={s.immEmoji}>⚡</span>
            <div style={s.immText}>
              <span style={s.immLabel}>지금 바로 받기</span>
              <span style={s.immDesc}>채널 설정 후 즉시 발송</span>
            </div>
            {active && (
              <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} style={{ ...s.checkBadge, position: 'static', marginLeft: 'auto' }}>
                <Check size={10} />
              </motion.div>
            )}
          </motion.button>
        )
      })()}

      {/* 구분선 */}
      <div style={s.orDivider}>
        <span style={s.orLine} />
        <span style={s.orText}>또는 나중에</span>
        <span style={s.orLine} />
      </div>

      {/* 날짜 선택 (4개) */}
      <div style={s.grid4}>
        {DATE_OPTIONS.filter(o => !o.immediate).map(opt => {
          const active = dateOpt === opt.label
          return (
            <motion.button key={opt.label}
              whileHover={{ scale: 1.04, y: -2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setDateOpt(opt.label)}
              style={{ ...s.optBtn, ...(active ? s.optActive : {}) }}
            >
              <span style={s.optEmoji}>{opt.emoji}</span>
              <span style={s.optLabel}>{opt.label}</span>
              <span style={s.optDate}>{formatDate(getScheduledDate(opt))}</span>
              {active && (
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} style={s.checkBadge}>
                  <Check size={10} />
                </motion.div>
              )}
            </motion.button>
          )
        })}
      </div>

      {/* 채널 선택 */}
      <AnimatePresence>
        {dateOpt && (
          <motion.div
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
          >
            <p style={{ ...s.label, marginTop: 28, marginBottom: 12, textAlign: 'center' }}>전송 채널</p>
            <div style={s.grid3}>
              {CHANNELS.map(ch => {
                const active = channel === ch.id
                return (
                  <motion.button key={ch.id}
                    whileHover={{ scale: 1.03, y: -1 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => handleChannelSelect(ch.id)}
                    style={{ ...s.chBtn, ...(active ? s.chActive : {}) }}
                  >
                    <span style={s.chEmoji}>{ch.emoji}</span>
                    <span style={s.chLabel}>{ch.label}</span>
                    <span style={s.chDesc}>{ch.desc}</span>
                    {active && (
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} style={s.checkBadge}>
                        <Check size={10} />
                      </motion.div>
                    )}
                  </motion.button>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 채널별 인증 / 입력 */}
      <AnimatePresence mode="wait">
        {dateOpt && channel && (
          <motion.div key={channel}
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            style={s.actions}
          >
            {/* 카카오 */}
            {channel === 'kakao' && (
              authStep !== 'done' ? (
                <motion.button
                  whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                  onClick={handleKakaoLogin}
                  disabled={authStep === 'waiting'}
                  style={s.kakaoBtn}
                >
                  <span style={{ fontSize: 20 }}>💬</span>
                  {authStep === 'waiting' ? '로그인 창을 확인해주세요...' : '카카오로 로그인'}
                </motion.button>
              ) : (
                <p style={s.authDone}>✓ 카카오 로그인 완료</p>
              )
            )}

            {/* 디스코드 */}
            {channel === 'discord' && (
              <div style={s.inputWrap}>
                <p style={s.inputLabel}>🎮 Discord 웹훅 URL</p>
                <input
                  type="text"
                  placeholder="https://discord.com/api/webhooks/..."
                  value={discordWebhook}
                  onChange={e => setDiscordWebhook(e.target.value)}
                  style={s.input}
                />
                <p style={s.inputHint}>채널 설정 → 연동 → 웹후크 → URL 복사</p>
              </div>
            )}

            {/* 이메일 */}
            {channel === 'email' && (
              <div style={s.inputWrap}>
                <p style={s.inputLabel}>📧 수신 이메일 주소</p>
                <input
                  type="email"
                  placeholder="example@gmail.com"
                  value={targetEmail}
                  onChange={e => setTargetEmail(e.target.value)}
                  style={s.input}
                />
                <p style={s.inputHint}>.env에 SMTP_USER / SMTP_PASSWORD 설정 필요 (Gmail 앱 비밀번호)</p>
              </div>
            )}

            {/* 예약 버튼 */}
            {canSchedule() && (
              <motion.button
                initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                whileHover={{ scale: 1.03, boxShadow: '0 8px 30px rgba(196,168,130,0.35)' }}
                whileTap={{ scale: 0.97 }}
                onClick={handleSchedule}
                style={{ ...s.scheduleBtn, marginTop: channel === 'kakao' ? 14 : 20 }}
              >
                <Clock size={16} style={{ marginRight: 8 }} />
                {DATE_OPTIONS.find(o => o.label === dateOpt)?.immediate ? '지금 바로 받기' : `${dateOpt}에 받기`}
              </motion.button>
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
  header:  { textAlign: 'center', marginBottom: 28 },
  label:   { color: '#c4a882', fontSize: 11, letterSpacing: 2.5, textTransform: 'uppercase', fontWeight: 500, marginBottom: 10 },
  desc:    { color: '#6a5a52', fontSize: 14 },

  immediateBtn: {
    display: 'flex', alignItems: 'center', gap: 16,
    width: '100%', padding: '16px 22px', marginBottom: 4,
    background: 'rgba(255,220,80,0.06)',
    border: '1px solid rgba(255,200,50,0.2)',
    borderRadius: 16, cursor: 'pointer', transition: 'all 0.2s',
  },
  immediateActive: {
    background: 'rgba(255,200,50,0.14)',
    border: '1px solid rgba(255,200,50,0.55)',
    boxShadow: '0 4px 20px rgba(255,200,50,0.12)',
  },
  immEmoji: { fontSize: 28 },
  immText:  { display: 'flex', flexDirection: 'column', gap: 3, textAlign: 'left' },
  immLabel: { color: '#f5e080', fontSize: 14, fontWeight: 600, fontFamily: "'Noto Sans KR', sans-serif" },
  immDesc:  { color: '#7a6a44', fontSize: 12, fontFamily: "'Noto Sans KR', sans-serif" },

  orDivider: { display: 'flex', alignItems: 'center', gap: 12, margin: '16px 0' },
  orLine:    { flex: 1, height: 1, background: 'rgba(196,168,130,0.15)' },
  orText:    { color: '#5a4a44', fontSize: 11, letterSpacing: 1.5, fontFamily: "'Noto Sans KR', sans-serif" },

  grid4: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 8 },
  grid3: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 8 },

  optBtn: {
    position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
    padding: '18px 10px', background: 'rgba(255,248,240,0.04)',
    border: '1px solid rgba(196,168,130,0.15)', borderRadius: 16, cursor: 'pointer', transition: 'all 0.2s',
  },
  optActive: {
    background: 'rgba(196,168,130,0.12)', border: '1px solid rgba(196,168,130,0.5)',
    boxShadow: '0 4px 20px rgba(196,168,130,0.15)',
  },
  optEmoji: { fontSize: 26 },
  optLabel: { color: '#f0e0cc', fontSize: 13, fontWeight: 500, fontFamily: "'Noto Sans KR', sans-serif" },
  optDate:  { color: '#6a5a52', fontSize: 11, fontFamily: "'Noto Sans KR', sans-serif" },

  chBtn: {
    position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
    padding: '16px 10px', background: 'rgba(255,248,240,0.04)',
    border: '1px solid rgba(196,168,130,0.15)', borderRadius: 16, cursor: 'pointer', transition: 'all 0.2s',
  },
  chActive: {
    background: 'rgba(196,168,130,0.12)', border: '1px solid rgba(196,168,130,0.5)',
    boxShadow: '0 4px 20px rgba(196,168,130,0.15)',
  },
  chEmoji: { fontSize: 24 },
  chLabel: { color: '#f0e0cc', fontSize: 13, fontWeight: 500, fontFamily: "'Noto Sans KR', sans-serif" },
  chDesc:  { color: '#6a5a52', fontSize: 10, fontFamily: "'Noto Sans KR', sans-serif", textAlign: 'center' },

  checkBadge: {
    position: 'absolute', top: 8, right: 8,
    background: '#c4a882', borderRadius: '50%',
    width: 18, height: 18, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#1a0f0a',
  },

  actions: { marginTop: 24, textAlign: 'center' },

  kakaoBtn: {
    display: 'inline-flex', alignItems: 'center', gap: 10,
    background: '#FEE500', border: 'none', borderRadius: 14,
    padding: '13px 32px', fontSize: 15, fontWeight: 600,
    color: '#1a1a1a', cursor: 'pointer', fontFamily: "'Noto Sans KR', sans-serif",
    boxShadow: '0 4px 20px rgba(254,229,0,0.25)',
  },
  authDone: { color: '#c4a882', fontSize: 13, marginBottom: 14 },

  inputWrap:  { textAlign: 'left', maxWidth: 440, margin: '0 auto' },
  inputLabel: { color: '#c4a882', fontSize: 12, letterSpacing: 1, marginBottom: 10, fontFamily: "'Noto Sans KR', sans-serif" },
  input: {
    width: '100%', boxSizing: 'border-box',
    background: 'rgba(255,248,240,0.06)', border: '1px solid rgba(196,168,130,0.25)',
    borderRadius: 10, padding: '11px 16px',
    color: '#f0e0cc', fontSize: 14, fontFamily: "'Noto Sans KR', sans-serif",
    outline: 'none',
  },
  inputHint: { color: '#5a4a44', fontSize: 11, marginTop: 8, fontFamily: "'Noto Sans KR', sans-serif" },

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
    width: '100%', background: 'rgba(196,168,130,0.06)',
    border: '1px solid rgba(196,168,130,0.2)',
    borderRadius: 24, padding: '40px', marginTop: 16, textAlign: 'center',
  },
  doneIcon:  { fontSize: 48, marginBottom: 16 },
  doneTitle: { fontFamily: "'Noto Serif KR', serif", fontSize: 22, color: '#f5ebe0', marginBottom: 12 },
  doneDesc:  { color: '#8a7065', fontSize: 15, lineHeight: 1.8, fontFamily: "'Noto Sans KR', sans-serif" },
}
