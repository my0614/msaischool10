import { useState } from "react";

export default function TodoPage() {
  const [todos, setTodos] = useState([
    { id: 1, text: "React 컴포넌트 만들기", done: true },
    { id: 2, text: "팀 소개 페이지 완성하기", done: false },
    { id: 3, text: "투두리스트 기능 구현하기", done: false },
  ]);
  const [input, setInput] = useState("");

  function addTodo() {
    const text = input.trim();
    if (!text) return;
    setTodos(t => [...t, { id: Date.now(), text, done: false }]);
    setInput("");
  }

  function toggleTodo(id) {
    setTodos(t => t.map(todo => todo.id === id ? { ...todo, done: !todo.done } : todo));
  }

  function deleteTodo(id) {
    setTodos(t => t.filter(todo => todo.id !== id));
  }

  const done  = todos.filter(t => t.done).length;
  const total = todos.length;

  return (
    <div style={s.page}>
      <div style={s.card}>
        {/* 헤더 */}
        <div style={s.header}>
          <h1 style={s.title}>투두리스트</h1>
          <span style={s.progress}>{done} / {total} 완료</span>
        </div>

        {/* 진행 바 */}
        <div style={s.barBg}>
          <div style={{ ...s.barFill, width: total ? `${(done / total) * 100}%` : "0%" }} />
        </div>

        {/* 입력 */}
        <div style={s.inputRow}>
          <input
            style={s.input}
            placeholder="할 일을 입력하세요"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && addTodo()}
          />
          <button style={s.addBtn} onClick={addTodo}>추가</button>
        </div>

        {/* 목록 */}
        <ul style={s.list}>
          {todos.length === 0 && (
            <p style={s.empty}>할 일이 없습니다 🎉</p>
          )}
          {todos.map(todo => (
            <li key={todo.id} style={s.item}>
              <button
                style={{ ...s.check, ...(todo.done ? s.checkDone : {}) }}
                onClick={() => toggleTodo(todo.id)}
              >
                {todo.done ? "✓" : ""}
              </button>
              <span style={{ ...s.text, ...(todo.done ? s.textDone : {}) }}>
                {todo.text}
              </span>
              <button style={s.del} onClick={() => deleteTodo(todo.id)}>✕</button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

const s = {
  page: {
    display: "flex", justifyContent: "center",
    padding: "80px 20px 60px",
    minHeight: "100vh",
  },
  card: {
    width: "100%", maxWidth: 520,
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: 24, padding: "36px 32px",
    display: "flex", flexDirection: "column", gap: 20,
    height: "fit-content",
    boxShadow: "0 8px 40px rgba(0,0,0,0.3)",
  },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  title:  { color: "#e2e8f0", fontSize: 22, fontWeight: 700 },
  progress: { color: "#64748b", fontSize: 13 },
  barBg:  { height: 6, background: "rgba(255,255,255,0.07)", borderRadius: 99 },
  barFill: { height: "100%", background: "linear-gradient(90deg,#6366f1,#a5b4fc)", borderRadius: 99, transition: "width 0.35s ease" },
  inputRow: { display: "flex", gap: 10 },
  input: {
    flex: 1, background: "rgba(255,255,255,0.06)",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 12, padding: "11px 16px",
    color: "#e2e8f0", fontSize: 14, fontFamily: "inherit", outline: "none",
  },
  addBtn: {
    background: "rgba(99,102,241,0.25)",
    border: "1px solid rgba(99,102,241,0.5)",
    borderRadius: 12, padding: "11px 20px",
    color: "#a5b4fc", fontSize: 14, cursor: "pointer", fontFamily: "inherit",
    whiteSpace: "nowrap",
  },
  list:  { listStyle: "none", display: "flex", flexDirection: "column", gap: 8 },
  empty: { color: "#475569", textAlign: "center", padding: "20px 0", fontSize: 14 },
  item: {
    display: "flex", alignItems: "center", gap: 12,
    background: "rgba(255,255,255,0.03)",
    border: "1px solid rgba(255,255,255,0.07)",
    borderRadius: 12, padding: "12px 14px",
  },
  check: {
    width: 22, height: 22, borderRadius: 6, flexShrink: 0,
    background: "transparent", border: "2px solid rgba(255,255,255,0.2)",
    cursor: "pointer", color: "#fff", fontSize: 12, fontWeight: 700,
    display: "flex", alignItems: "center", justifyContent: "center",
  },
  checkDone: { background: "#6366f1", border: "2px solid #6366f1" },
  text: { flex: 1, color: "#cbd5e1", fontSize: 14 },
  textDone: { textDecoration: "line-through", color: "#475569" },
  del: {
    background: "transparent", border: "none",
    color: "#475569", cursor: "pointer", fontSize: 13,
    padding: "2px 4px",
  },
};
