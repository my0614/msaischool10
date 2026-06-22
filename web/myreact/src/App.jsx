import { useState } from "react";
import TeamPage from "./pages/TeamPage";
import CounterPage from "./pages/CounterPage";
import TodoPage from "./pages/TodoPage";
import BoardPage from "./pages/BoardPage";

const PAGES = [
  { id: "team",    label: "팀 소개" },
  { id: "counter", label: "카운터" },
  { id: "todo",    label: "투두리스트" },
  { id: "board",   label: "게시판" },
];

export default function App() {
  const [page, setPage] = useState("team");

  return (
    <div style={{ minHeight: "100vh", background: "#0f0f1a" }}>
      {/* 상단 중앙 네비게이션 */}
      <nav style={s.nav}>
        {PAGES.map((p) => (
          <button
            key={p.id}
            onClick={() => setPage(p.id)}
            style={{ ...s.btn, ...(page === p.id ? s.btnActive : {}) }}
          >
            {p.label}
          </button>
        ))}
      </nav>

      {/* 네비게이션 높이만큼 상단 여백 */}
      <div style={{ paddingTop: 64 }}>
        {page === "team"    && <TeamPage />}
        {page === "counter" && <CounterPage />}
        {page === "todo"    && <TodoPage />}
        {page === "board"   && <BoardPage />}
      </div>
    </div>
  );
}

const s = {
  nav: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    zIndex: 100,
    display: "flex",
    justifyContent: "center",
    gap: 8,
    padding: "14px 24px",
    background: "rgba(15,15,26,0.85)",
    backdropFilter: "blur(12px)",
    borderBottom: "1px solid rgba(255,255,255,0.07)",
  },
  btn: {
    background: "transparent",
    border: "1px solid transparent",
    borderRadius: 10,
    padding: "7px 20px",
    color: "#64748b",
    fontSize: 14,
    cursor: "pointer",
    fontFamily: "inherit",
    transition: "all 0.15s",
  },
  btnActive: {
    background: "rgba(99,102,241,0.15)",
    border: "1px solid rgba(99,102,241,0.4)",
    color: "#a5b4fc",
  },
};
