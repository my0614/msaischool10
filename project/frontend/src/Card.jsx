import { forwardRef } from 'react'

const Card = forwardRef(function Card({ result }, ref) {
  const { emotions, keywords, letter, date, qr_b64 } = result

  return (
    <div ref={ref} style={c.root}>
      {/* 테두리 장식 */}
      <div style={c.border} />

      {/* 상단 장식 */}
      <div style={c.topDeco}>
        <span style={c.decoLine} />
        <span style={c.decoText}>✦ TIME CAPSULE ✦</span>
        <span style={c.decoLine} />
      </div>

      {/* 제목 */}
      <div style={c.titleArea}>
        <div style={c.envelope}>💌</div>
        <h1 style={c.title}>Dear Me</h1>
        <p style={c.date}>{date}</p>
      </div>

      {/* 감정 태그 */}
      <div style={c.tagRow}>
        {emotions.map((e, i) => (
          <span key={i} style={c.emoTag}>{e}</span>
        ))}
      </div>

      {/* 키워드 */}
      <div style={c.kwRow}>
        {keywords.map((k, i) => (
          <span key={i} style={c.kwTag}>#{k}</span>
        ))}
      </div>

      {/* 구분선 */}
      <div style={c.dividerWrap}>
        <span style={c.divLine} />
        <span style={c.divDot}>✦</span>
        <span style={c.divLine} />
      </div>

      {/* 편지 본문 */}
      <div style={c.letterArea}>
        {letter.split('\n').map((line, i) => (
          <p key={i} style={{ marginBottom: line === '' ? 16 : 2, minHeight: line === '' ? 16 : 'auto' }}>
            {line}
          </p>
        ))}
      </div>

      {/* 하단: QR + 장식 */}
      <div style={c.footer}>
        <div style={c.footerLeft}>
          <div style={c.footerDeco}>✦ Time Capsule Letter ✦</div>
        </div>
        <div style={c.qrWrap}>
          <img src={`data:image/png;base64,${qr_b64}`} alt="QR" style={c.qrImg} />
          <p style={c.qrLabel}>편지 보기</p>
        </div>
      </div>
    </div>
  )
})

export default Card

const CREAM = '#FDF6EC'
const DARK  = '#2C1A0E'
const MID   = '#7A5C3A'
const GOLD  = '#C4985A'
const LGOLD = '#E8D5B0'

const c = {
  root: {
    width: 560,
    background: `linear-gradient(160deg, ${CREAM} 0%, #F5E8D0 100%)`,
    borderRadius: 20,
    padding: '48px 44px 40px',
    fontFamily: "'Noto Serif KR', serif",
    color: DARK,
    position: 'relative',
    boxSizing: 'border-box',
  },
  border: {
    position: 'absolute', inset: 8,
    border: `1px solid ${LGOLD}`,
    borderRadius: 14, pointerEvents: 'none',
  },
  topDeco: {
    display: 'flex', alignItems: 'center', gap: 10,
    marginBottom: 32,
  },
  decoLine: { flex: 1, height: 1, background: LGOLD },
  decoText: { fontSize: 10, letterSpacing: 3, color: GOLD, whiteSpace: 'nowrap', fontFamily: "'Noto Sans KR', sans-serif" },
  titleArea: { textAlign: 'center', marginBottom: 24 },
  envelope: { fontSize: 40, marginBottom: 8, lineHeight: 1 },
  title: {
    fontFamily: "'Noto Serif KR', serif",
    fontSize: 42, fontWeight: 300,
    color: DARK, margin: '0 0 8px', letterSpacing: -0.5,
  },
  date: { fontSize: 12, color: MID, letterSpacing: 1, fontFamily: "'Noto Sans KR', sans-serif" },
  tagRow: { display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', marginBottom: 10 },
  emoTag: {
    background: 'rgba(196,152,90,0.12)',
    border: `1px solid ${LGOLD}`,
    borderRadius: 20, padding: '5px 14px',
    fontSize: 14, color: DARK,
    fontFamily: "'Noto Sans KR', sans-serif",
  },
  kwRow: { display: 'flex', gap: 10, flexWrap: 'wrap', justifyContent: 'center', marginBottom: 28 },
  kwTag: { fontSize: 12, color: GOLD, fontFamily: "'Noto Sans KR', sans-serif", letterSpacing: 0.5 },
  dividerWrap: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 28 },
  divLine: { flex: 1, height: 1, background: LGOLD },
  divDot: { color: GOLD, fontSize: 10 },
  letterArea: {
    fontSize: 14, lineHeight: 2.1, color: '#3a2510',
    background: 'rgba(255,255,255,0.45)',
    borderRadius: 12, padding: '20px 24px',
    marginBottom: 32,
    border: `1px solid rgba(232,213,176,0.6)`,
  },
  footer: { display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' },
  footerLeft: { flex: 1 },
  footerDeco: { fontSize: 10, color: GOLD, letterSpacing: 2, fontFamily: "'Noto Sans KR', sans-serif" },
  qrWrap: { textAlign: 'center' },
  qrImg: { width: 80, height: 80, borderRadius: 8, border: `1px solid ${LGOLD}`, display: 'block' },
  qrLabel: { fontSize: 9, color: MID, marginTop: 4, fontFamily: "'Noto Sans KR', sans-serif", letterSpacing: 0.5 },
}
