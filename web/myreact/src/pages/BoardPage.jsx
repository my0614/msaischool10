import { useState } from "react";

const INITIAL_POSTS = [
  { id: 1, title: "프로젝트 킥오프 미팅 후기", author: "김민영", date: "2026.06.10", views: 42, content: "오늘 첫 킥오프 미팅을 가졌습니다. 팀원들과 방향성을 맞추고 역할 분담을 완료했어요. 앞으로 잘 부탁드립니다!" },
  { id: 2, title: "React 상태관리 스터디 공유",  author: "이지은", date: "2026.06.14", views: 28, content: "useState, useReducer, Context API를 비교 정리했습니다. 소규모 프로젝트에는 useState + Context 조합이 적합하다는 결론을 내렸습니다." },
  { id: 3, title: "팀 회식 장소 투표 결과",       author: "박준혁", date: "2026.06.18", views: 55, content: "투표 결과 삼겹살 집이 1위! 다음 주 금요일 저녁 7시에 만나요 🍖" },
];

export default function BoardPage() {
  const [posts, setPosts]       = useState(INITIAL_POSTS);
  const [selected, setSelected] = useState(null);   // 상세보기
  const [writing, setWriting]   = useState(false);  // 글쓰기
  const [form, setForm]         = useState({ title: "", author: "", content: "" });

  function openPost(post) {
    setPosts(ps => ps.map(p => p.id === post.id ? { ...p, views: p.views + 1 } : p));
    setSelected({ ...post, views: post.views + 1 });
  }

  function submitPost() {
    if (!form.title.trim() || !form.author.trim() || !form.content.trim()) return;
    const newPost = {
      id:      Date.now(),
      title:   form.title.trim(),
      author:  form.author.trim(),
      content: form.content.trim(),
      date:    new Date().toLocaleDateString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit" }).replace(/\. /g, ".").replace(".", "").slice(0, -1),
      views:   0,
    };
    setPosts(ps => [newPost, ...ps]);
    setForm({ title: "", author: "", content: "" });
    setWriting(false);
  }

  function deletePost(id) {
    setPosts(ps => ps.filter(p => p.id !== id));
    setSelected(null);
  }

  // ── 상세보기 ──
  if (selected) return (
    <div style={s.page}>
      <div style={s.card}>
        <button style={s.backBtn} onClick={() => setSelected(null)}>← 목록으로</button>
        <div style={s.detailHeader}>
          <h2 style={s.detailTitle}>{selected.title}</h2>
          <div style={s.meta}>
            <span style={s.metaItem}>✍️ {selected.author}</span>
            <span style={s.metaItem}>📅 {selected.date}</span>
            <span style={s.metaItem}>👁 {selected.views}</span>
          </div>
        </div>
        <div style={s.divider} />
        <p style={s.detailContent}>{selected.content}</p>
        <div style={{ textAlign: "right", marginTop: 24 }}>
          <button style={s.delBtn} onClick={() => deletePost(selected.id)}>삭제</button>
        </div>
      </div>
    </div>
  );

  // ── 글쓰기 ──
  if (writing) return (
    <div style={s.page}>
      <div style={s.card}>
        <button style={s.backBtn} onClick={() => setWriting(false)}>← 취소</button>
        <h2 style={s.sectionTitle}>새 글 작성</h2>
        <div style={s.formGroup}>
          <label style={s.label}>제목</label>
          <input style={s.input} placeholder="제목을 입력하세요" value={form.title}
            onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
        </div>
        <div style={s.formGroup}>
          <label style={s.label}>작성자</label>
          <input style={s.input} placeholder="이름을 입력하세요" value={form.author}
            onChange={e => setForm(f => ({ ...f, author: e.target.value }))} />
        </div>
        <div style={s.formGroup}>
          <label style={s.label}>내용</label>
          <textarea style={s.textarea} placeholder="내용을 입력하세요" rows={6} value={form.content}
            onChange={e => setForm(f => ({ ...f, content: e.target.value }))} />
        </div>
        <button style={s.submitBtn} onClick={submitPost}>등록하기</button>
      </div>
    </div>
  );

  // ── 목록 ──
  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.listHeader}>
          <h2 style={s.sectionTitle}>게시판</h2>
          <button style={s.writeBtn} onClick={() => setWriting(true)}>+ 글쓰기</button>
        </div>

        {posts.length === 0 && <p style={s.empty}>게시글이 없습니다.</p>}

        <table style={s.table}>
          <thead>
            <tr>
              {["번호", "제목", "작성자", "날짜", "조회"].map(h => (
                <th key={h} style={s.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {posts.map((post, i) => (
              <tr key={post.id} style={s.tr} onClick={() => openPost(post)}>
                <td style={{ ...s.td, ...s.tdNum }}>{posts.length - i}</td>
                <td style={{ ...s.td, ...s.tdTitle }}>{post.title}</td>
                <td style={{ ...s.td, ...s.tdMeta }}>{post.author}</td>
                <td style={{ ...s.td, ...s.tdMeta }}>{post.date}</td>
                <td style={{ ...s.td, ...s.tdMeta }}>{post.views}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const s = {
  page: { display: "flex", justifyContent: "center", padding: "40px 20px 60px" },
  card: {
    width: "100%", maxWidth: 720,
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: 20, padding: "32px 28px",
    boxShadow: "0 8px 40px rgba(0,0,0,0.3)",
  },
  listHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 },
  sectionTitle: { color: "#e2e8f0", fontSize: 20, fontWeight: 700 },
  writeBtn: {
    background: "rgba(99,102,241,0.2)", border: "1px solid rgba(99,102,241,0.4)",
    borderRadius: 10, padding: "8px 18px", color: "#a5b4fc",
    fontSize: 14, cursor: "pointer", fontFamily: "inherit",
  },
  table: { width: "100%", borderCollapse: "collapse" },
  th: {
    padding: "10px 12px", textAlign: "left",
    color: "#475569", fontSize: 12, fontWeight: 600, letterSpacing: 0.5,
    borderBottom: "1px solid rgba(255,255,255,0.08)",
  },
  tr: {
    cursor: "pointer", transition: "background 0.12s",
    borderBottom: "1px solid rgba(255,255,255,0.05)",
  },
  td:       { padding: "13px 12px", fontSize: 14, color: "#cbd5e1" },
  tdNum:    { color: "#475569", width: 48 },
  tdTitle:  { color: "#e2e8f0", fontWeight: 500 },
  tdMeta:   { color: "#64748b", fontSize: 13 },
  backBtn: {
    background: "transparent", border: "none",
    color: "#64748b", cursor: "pointer", fontSize: 13,
    padding: "0 0 20px", fontFamily: "inherit",
  },
  detailHeader: { marginBottom: 16 },
  detailTitle:  { color: "#e2e8f0", fontSize: 20, fontWeight: 700, marginBottom: 12 },
  meta: { display: "flex", gap: 16 },
  metaItem: { color: "#475569", fontSize: 13 },
  divider: { height: 1, background: "rgba(255,255,255,0.08)", margin: "16px 0 24px" },
  detailContent: { color: "#94a3b8", fontSize: 15, lineHeight: 1.9, whiteSpace: "pre-wrap" },
  delBtn: {
    background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)",
    borderRadius: 8, padding: "7px 16px", color: "#f87171",
    fontSize: 13, cursor: "pointer", fontFamily: "inherit",
  },
  formGroup: { display: "flex", flexDirection: "column", gap: 6, marginBottom: 16 },
  label: { color: "#64748b", fontSize: 12, fontWeight: 600, letterSpacing: 0.5 },
  input: {
    background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 10, padding: "10px 14px", color: "#e2e8f0",
    fontSize: 14, fontFamily: "inherit", outline: "none",
  },
  textarea: {
    background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 10, padding: "10px 14px", color: "#e2e8f0",
    fontSize: 14, fontFamily: "inherit", outline: "none", resize: "vertical",
  },
  submitBtn: {
    width: "100%", background: "rgba(99,102,241,0.25)",
    border: "1px solid rgba(99,102,241,0.5)",
    borderRadius: 12, padding: "12px", color: "#a5b4fc",
    fontSize: 15, fontWeight: 600, cursor: "pointer", fontFamily: "inherit", marginTop: 8,
  },
  empty: { color: "#475569", textAlign: "center", padding: "32px 0", fontSize: 14 },
};
