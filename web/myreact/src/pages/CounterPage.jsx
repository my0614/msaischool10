import { useState } from "react";

export default function CounterPage() {
  const [count, setCount] = useState(0);

  return (
    <div style={s.page}>
      <h1 style={s.title}>카운터</h1>
      <div style={s.card}>
        <span style={s.count}>{count}</span>
        <div style={s.row}>
          <button style={{ ...s.btn, ...s.btnMinus }} onClick={() => setCount(c => c - 1)}>−</button>
          <button style={{ ...s.btn, ...s.btnReset }} onClick={() => setCount(0)}>Reset</button>
          <button style={{ ...s.btn, ...s.btnPlus }}  onClick={() => setCount(c => c + 1)}>+</button>
        </div>
      </div>
    </div>
  );
}

const s = {
  page: {
    display: "flex", flexDirection: "column",
    alignItems: "center", justifyContent: "center",
    minHeight: "100vh", gap: 32,
  },
  title: {
    color: "#e2e8f0", fontSize: 28, fontWeight: 600,
    letterSpacing: 1,
  },
  card: {
    background: "rgba(255,255,255,0.05)",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: 24, padding: "48px 64px",
    display: "flex", flexDirection: "column",
    alignItems: "center", gap: 36,
    boxShadow: "0 8px 40px rgba(0,0,0,0.3)",
  },
  count: {
    fontSize: 96, fontWeight: 700, color: "#a5b4fc",
    lineHeight: 1, minWidth: 160, textAlign: "center",
    fontVariantNumeric: "tabular-nums",
  },
  row: { display: "flex", gap: 16, alignItems: "center" },
  btn: {
    border: "none", borderRadius: 12, cursor: "pointer",
    fontSize: 18, fontWeight: 600, fontFamily: "inherit",
    transition: "transform 0.1s, opacity 0.1s",
  },
  btnMinus: {
    width: 56, height: 56, background: "rgba(239,68,68,0.15)",
    color: "#f87171", border: "1px solid rgba(239,68,68,0.3)",
  },
  btnReset: {
    padding: "14px 28px", background: "rgba(255,255,255,0.07)",
    color: "#94a3b8", border: "1px solid rgba(255,255,255,0.12)",
    fontSize: 15,
  },
  btnPlus: {
    width: 56, height: 56, background: "rgba(99,102,241,0.2)",
    color: "#a5b4fc", border: "1px solid rgba(99,102,241,0.4)",
  },
};
