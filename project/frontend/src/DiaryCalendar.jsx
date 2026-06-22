import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronLeft, ChevronRight, X } from 'lucide-react'

const API = `http://${window.location.hostname}:8000`
const DAYS = ['일', '월', '화', '수', '목', '금', '토']

function formatKorDate(isoDate) {
  const [y, m, d] = isoDate.split('-')
  return `${y}년 ${parseInt(m)}월 ${parseInt(d)}일`
}

export default function DiaryCalendar({ stateKey, onClose }) {
  const now = new Date()
  const [year, setYear]           = useState(now.getFullYear())
  const [month, setMonth]         = useState(now.getMonth())       // 0-indexed
  const [markedDates, setMarked]  = useState({})                   // { "2026-06-22": 2 }
  const [selectedDate, setSelDate]= useState(null)
  const [entries, setEntries]     = useState([])
  const [loadingE, setLoadingE]   = useState(false)

  useEffect(() => {
    fetch(`${API}/api/calendar?state=${stateKey}`)
      .then(r => r.json())
      .then(data => {
        if (!data.dates) return
        const map = {}
        data.dates.forEach(d => { map[d.date] = d.count })
        setMarked(map)
      })
      .catch(() => {})
  }, [stateKey])

  async function handleDateClick(isoDate) {
    if (!markedDates[isoDate]) return
    setSelDate(isoDate)
    setLoadingE(true)
    const data = await fetch(`${API}/api/diary/${isoDate}?state=${stateKey}`)
      .then(r => r.json())
      .catch(() => ({}))
    setEntries(data.entries || [])
    setLoadingE(false)
  }

  function prevMonth() {
    setSelDate(null); setEntries([])
    if (month === 0) { setYear(y => y - 1); setMonth(11) } else setMonth(m => m - 1)
  }
  function nextMonth() {
    setSelDate(null); setEntries([])
    if (month === 11) { setYear(y => y + 1); setMonth(0) } else setMonth(m => m + 1)
  }

  const firstDay    = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const todayISO    = now.toISOString().slice(0, 10)

  const cells = []
  for (let i = 0; i < firstDay; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) cells.push(d)

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={s.overlay}
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, x: 60 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 60 }}
        transition={{ type: 'spring', damping: 28, stiffness: 280 }}
        style={s.panel}
        onClick={e => e.stopPropagation()}
      >
        {/* 패널 헤더 */}
        <div style={s.panelHeader}>
          <span style={s.panelTitle}>📅 일기 캘린더</span>
          <button onClick={onClose} style={s.closeBtn}><X size={17} /></button>
        </div>

        {/* 월 네비게이션 */}
        <div style={s.monthNav}>
          <button onClick={prevMonth} style={s.navBtn}><ChevronLeft size={16} /></button>
          <span style={s.monthLabel}>{year}년 {month + 1}월</span>
          <button onClick={nextMonth} style={s.navBtn}><ChevronRight size={16} /></button>
        </div>

        {/* 요일 헤더 */}
        <div style={s.weekRow}>
          {DAYS.map((d, i) => (
            <div key={d} style={{
              ...s.weekDay,
              color: i === 0 ? '#e07878' : i === 6 ? '#7888e0' : '#5a4a44',
            }}>
              {d}
            </div>
          ))}
        </div>

        {/* 날짜 그리드 */}
        <div style={s.grid}>
          {cells.map((day, i) => {
            if (!day) return <div key={`_${i}`} />
            const iso      = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
            const hasEntry = !!markedDates[iso]
            const isToday  = iso === todayISO
            const isSel    = iso === selectedDate
            const count    = markedDates[iso] || 0
            const dow      = new Date(year, month, day).getDay()
            return (
              <motion.button
                key={iso}
                whileHover={hasEntry ? { scale: 1.12 } : {}}
                whileTap={hasEntry ? { scale: 0.92 } : {}}
                onClick={() => handleDateClick(iso)}
                style={{
                  ...s.dayBtn,
                  ...(isToday ? s.todayBtn : {}),
                  ...(isSel   ? s.selBtn   : {}),
                  cursor: hasEntry ? 'pointer' : 'default',
                }}
              >
                <span style={{
                  fontSize: 13,
                  fontWeight: isToday || isSel ? 700 : 400,
                  color: isSel ? '#1a0f0a'
                       : isToday ? '#c4a882'
                       : dow === 0 ? '#c07070'
                       : dow === 6 ? '#7080c0'
                       : '#c0b0a0',
                }}>
                  {day}
                </span>
                {hasEntry && (
                  <div style={{ ...s.dot, background: isSel ? '#1a0f0a' : '#c4a882' }}>
                    {count > 1 && (
                      <span style={s.countBadge}>{count}</span>
                    )}
                  </div>
                )}
              </motion.button>
            )
          })}
        </div>

        {/* 범례 */}
        <div style={s.legend}>
          <div style={s.legendItem}>
            <div style={{ ...s.dot, background: '#c4a882', position: 'static' }} />
            <span>일기 있음</span>
          </div>
          <span style={{ color: '#4a3a32', fontSize: 11 }}>
            총 {Object.keys(markedDates).length}일 기록
          </span>
        </div>

        {/* 선택 날짜 일기 목록 */}
        <AnimatePresence>
          {selectedDate && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              style={s.entriesWrap}
            >
              <p style={s.entriesTitle}>{formatKorDate(selectedDate)}</p>

              {loadingE ? (
                <p style={s.loadingTxt}>불러오는 중...</p>
              ) : entries.length === 0 ? (
                <p style={s.loadingTxt}>일기가 없습니다.</p>
              ) : entries.map((entry, i) => (
                <motion.div
                  key={entry.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.07 }}
                  style={s.entryCard}
                >
                  <div style={s.emoRow}>
                    {entry.emotions.map((e, j) => (
                      <span key={j} style={s.emoTag}>{e}</span>
                    ))}
                    <span style={s.timeStamp}>
                      {entry.created_at.slice(11, 16)}
                    </span>
                  </div>
                  <p style={s.letterPreview}>{entry.letter}</p>
                  <p style={s.kwLine}>
                    {entry.keywords.map(k => `#${k}`).join('  ')}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  )
}

const s = {
  overlay: {
    position: 'fixed', inset: 0, zIndex: 200,
    background: 'rgba(10,5,3,0.65)',
    backdropFilter: 'blur(6px)',
    display: 'flex', justifyContent: 'flex-end',
  },
  panel: {
    width: '100%', maxWidth: 380,
    height: '100vh', overflowY: 'auto',
    background: 'linear-gradient(170deg,#1e1008 0%,#2d1a10 100%)',
    borderLeft: '1px solid rgba(196,168,130,0.15)',
    padding: '28px 22px 40px',
    display: 'flex', flexDirection: 'column',
  },
  panelHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: 28,
  },
  panelTitle: {
    color: '#c4a882', fontSize: 15, fontWeight: 600,
    fontFamily: "'Noto Sans KR', sans-serif", letterSpacing: 0.5,
  },
  closeBtn: {
    background: 'transparent', border: '1px solid rgba(196,168,130,0.2)',
    borderRadius: '50%', width: 30, height: 30,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    cursor: 'pointer', color: '#8a7065',
  },
  monthNav: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    marginBottom: 18,
  },
  navBtn: {
    background: 'rgba(255,248,240,0.04)', border: '1px solid rgba(196,168,130,0.2)',
    borderRadius: 8, padding: '5px 9px',
    cursor: 'pointer', color: '#8a7065',
    display: 'flex', alignItems: 'center',
  },
  monthLabel: {
    color: '#f0e0cc', fontSize: 16, fontWeight: 600,
    fontFamily: "'Noto Serif KR', serif",
  },
  weekRow: {
    display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)',
    marginBottom: 6,
  },
  weekDay: {
    textAlign: 'center', fontSize: 11,
    fontFamily: "'Noto Sans KR', sans-serif",
    paddingBottom: 8, letterSpacing: 0.5,
  },
  grid: {
    display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)',
    gap: 3, marginBottom: 16,
  },
  dayBtn: {
    position: 'relative',
    display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center',
    height: 42, borderRadius: 10,
    background: 'transparent', border: 'none',
    gap: 2, padding: 0,
  },
  todayBtn: {
    background: 'rgba(196,168,130,0.1)',
    border: '1px solid rgba(196,168,130,0.35)',
  },
  selBtn: {
    background: '#c4a882',
  },
  dot: {
    width: 5, height: 5, borderRadius: '50%',
    position: 'relative',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  countBadge: {
    position: 'absolute', top: -7, left: 5,
    background: '#8b6340', borderRadius: 6,
    fontSize: 8, color: '#fff',
    padding: '0 3px', lineHeight: '13px',
    whiteSpace: 'nowrap',
  },
  legend: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '10px 2px',
    borderBottom: '1px solid rgba(196,168,130,0.12)',
    marginBottom: 20,
  },
  legendItem: {
    display: 'flex', alignItems: 'center', gap: 7,
    color: '#6a5a52', fontSize: 11,
    fontFamily: "'Noto Sans KR', sans-serif",
  },
  entriesWrap: {
    display: 'flex', flexDirection: 'column',
  },
  entriesTitle: {
    color: '#c4a882', fontSize: 13, letterSpacing: 1,
    fontFamily: "'Noto Serif KR', serif",
    marginBottom: 14,
  },
  loadingTxt: {
    color: '#5a4a42', fontSize: 13, textAlign: 'center', padding: '20px 0',
    fontFamily: "'Noto Sans KR', sans-serif",
  },
  entryCard: {
    background: 'rgba(255,248,240,0.04)',
    border: '1px solid rgba(196,168,130,0.12)',
    borderRadius: 14, padding: '14px 16px',
    marginBottom: 12,
  },
  emoRow: {
    display: 'flex', alignItems: 'center', gap: 6,
    flexWrap: 'wrap', marginBottom: 10,
  },
  emoTag: {
    background: 'rgba(196,168,130,0.1)',
    border: '1px solid rgba(196,168,130,0.2)',
    borderRadius: 14, padding: '2px 10px',
    fontSize: 11, color: '#f0e0cc',
  },
  timeStamp: {
    marginLeft: 'auto', color: '#4a3a32', fontSize: 11,
    fontFamily: "'Noto Sans KR', sans-serif",
  },
  letterPreview: {
    color: '#c0a888', fontSize: 13, lineHeight: 1.85,
    fontFamily: "'Noto Serif KR', serif",
    marginBottom: 10,
    display: '-webkit-box',
    WebkitLineClamp: 5,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  },
  kwLine: {
    color: '#5a4a42', fontSize: 11,
    fontFamily: "'Noto Sans KR', sans-serif",
  },
}
