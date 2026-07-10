import { useEffect, useState } from "react";
import axios from "axios";
import "./PhilosopherPage.css";

// 위키백과 요약 API에는 없는 정보라 고정값으로 둔다
const PHILOSOPHERS = [
  { name: "소크라테스", wikiTitle: "소크라테스", nickname: "아테네의 등에" },
  { name: "플라톤", wikiTitle: "플라톤", nickname: "어깨 넓은 아리스토클레스" },
  { name: "아리스토텔레스", wikiTitle: "아리스토텔레스", nickname: "스타게이라의 현자" },
  { name: "칸트", wikiTitle: "임마누엘_칸트", nickname: "쾨니히스베르크의 시계" },
  { name: "니체", wikiTitle: "프리드리히_니체", nickname: "망치를 든 철학자" },
];

function truncate(text, max) {
  if (!text || text.length <= max) return text;
  return `${text.slice(0, max)}...`;
}

async function fetchPhilosophers() {
  const [results] = await Promise.all([
    Promise.all(
      PHILOSOPHERS.map(async (p) => {
        const { data } = await axios.get(
          `https://ko.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(p.wikiTitle)}`
        );
        return {
          name: p.name,
          nickname: p.nickname,
          intro: truncate(data.extract, 70),
          img: data.thumbnail?.source,
        };
      })
    ),
    new Promise((resolve) => setTimeout(resolve, 2000)),
  ]);
  return results;
}

const ICON_POSITIONS = [
  { top: "6%", left: "4%", size: 40, rotate: -18 },
  { top: "10%", left: "48%", size: 28, rotate: 12 },
  { top: "4%", left: "88%", size: 44, rotate: 20 },
  { top: "40%", left: "94%", size: 32, rotate: -10 },
  { top: "40%", left: "1%", size: 30, rotate: 15 },
];

function OwlIcon({ top, left, size, rotate }) {
  return (
    <svg
      viewBox="0 0 64 64"
      className="philo-icon"
      style={{
        top,
        left,
        width: size,
        height: size,
        transform: `rotate(${rotate}deg)`,
      }}
      fill="#FFFFFF"
    >
      <ellipse cx="32" cy="36" rx="18" ry="20" />
      <polygon points="14,14 24,26 8,26" />
      <polygon points="50,14 56,26 40,26" />
      <circle cx="24" cy="34" r="7" fill="#4B3F6B" />
      <circle cx="40" cy="34" r="7" fill="#4B3F6B" />
      <circle cx="24" cy="34" r="3" fill="#FFFFFF" />
      <circle cx="40" cy="34" r="3" fill="#FFFFFF" />
      <polygon points="32,40 28,46 36,46" fill="#4B3F6B" />
    </svg>
  );
}

function MemberCard({ name, intro, nickname, img, flipped, onToggle }) {
  return (
    <div
      className="philo-card"
      onClick={onToggle}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onToggle()}
    >
      <div className={`philo-card-inner ${flipped ? "is-flipped" : ""}`}>
        <div className="philo-card-face philo-card-front">
          <div className="philo-card-img">
            <img src={img} alt={name} />
          </div>
          <div className="philo-card-body">
            <h3 className="philo-card-name">{name}</h3>
            <p className="philo-card-meta">{intro}</p>
          </div>
        </div>
        <div className="philo-card-face philo-card-back">
          <p className="philo-card-back-label">별명</p>
          <h3 className="philo-card-back-nickname">{nickname}</h3>
          <p className="philo-card-back-name">{name}</p>
        </div>
      </div>
    </div>
  );
}

export default function PhilosopherPage() {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [flipped, setFlipped] = useState({});
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchPhilosophers()
      .then((data) => {
        if (cancelled) return;
        setMembers(data);
      })
      .catch(() => {
        if (!cancelled) setError("철학자 정보를 불러오지 못했어요.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [retryCount]);

  const toggleFlip = (name) => {
    setFlipped((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  return (
    <div className="philo-wrap">
      {ICON_POSITIONS.map((p, i) => (
        <OwlIcon key={i} {...p} />
      ))}

      <h1 className="philo-title">철학소년단</h1>

      {loading ? (
        <div className="philo-loading">
          <div className="philo-spinner" />
          <p>철학자들을 불러오는 중...</p>
        </div>
      ) : error ? (
        <div className="philo-loading">
          <p className="philo-error-text">{error}</p>
          <button
            type="button"
            className="philo-retry-btn"
            onClick={() => setRetryCount((c) => c + 1)}
          >
            다시 시도
          </button>
        </div>
      ) : (
        <div className="philo-grid">
          {members.map((m) => (
            <MemberCard
              key={m.name}
              {...m}
              flipped={!!flipped[m.name]}
              onToggle={() => toggleFlip(m.name)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
