import { useState } from "react";
import TeamPage from "./pages/TeamPage";
import CounterPage from "./pages/CounterPage";
import TodoPage from "./pages/TodoPage";

const PAGES = [
  { id: "team",    label: "팀 소개" },
  { id: "counter", label: "카운터" },
  { id: "todo",    label: "투두리스트" },
];

export default function App() {
  const [page, setPage] = useState("team");

  return (
    <div style={{ minHeight: "100vh", background: "#0f0f1a" }}>
      {/* 우측 상단 네비게이션 */}
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

      {/* 페이지 렌더링 */}
      {page === "team"    && <TeamPage />}
      {page === "counter" && <CounterPage />}
      {page === "todo"    && <TodoPage />}
    </div>
  );
}

const s = {
  nav: {
    position: "fixed",
    top: 20,
    right: 24,
    zIndex: 100,
    display: "flex",
    gap: 8,
  },
  btn: {
    background: "rgba(255,255,255,0.06)",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 10,
    padding: "8px 18px",
    color: "#94a3b8",
    fontSize: 14,
    cursor: "pointer",
    fontFamily: "inherit",
    transition: "all 0.15s",
  },
  btnActive: {
    background: "rgba(99,102,241,0.2)",
    border: "1px solid rgba(99,102,241,0.5)",
    color: "#a5b4fc",
  },
};
