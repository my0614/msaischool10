import { useState } from 'react'
import { members } from './info'
import './App.css'

function getAvatar(name, bgColor) {
  return `https://api.dicebear.com/9.x/adventurer/svg?seed=${encodeURIComponent(name)}&backgroundColor=${bgColor}`
}

function MemberCard({ member, onClick }) {
  return (
    <div className="card" onClick={() => onClick(member)}>
      <img src={getAvatar(member.name, member.bgColor)} alt={member.name} className="avatar" />
      <div className="badge">{member.role}</div>
      <h2 className="name">{member.name}</h2>
      <p className="department">{member.department}</p>
      <p className="description">{member.description}</p>
      <div className="skills">
        {member.skills.map((skill) => (
          <span key={skill} className="skill">{skill}</span>
        ))}
      </div>
    </div>
  )
}

function Modal({ member, onClose }) {
  if (!member) return null

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}>✕</button>
        <img src={getAvatar(member.name, member.bgColor)} alt={member.name} className="modal-avatar" />
        <div className="modal-badge">{member.role}</div>
        <h2 className="modal-name">{member.name}</h2>
        <p className="modal-department">{member.department}</p>
        <p className="modal-description">{member.description}</p>
        <div className="modal-section">
          <h3>스킬</h3>
          <div className="skills">
            {member.skills.map((skill) => (
              <span key={skill} className="skill">{skill}</span>
            ))}
          </div>
        </div>
        <div className="modal-section">
          <h3>연락처</h3>
          <div className="links">
            <a href={member.github} target="_blank" rel="noreferrer">GitHub</a>
            <a href={`mailto:${member.email}`}>이메일</a>
          </div>
        </div>
      </div>
    </div>
  )
}

function App() {
  const [selected, setSelected] = useState(null)

  return (
    <div className="page">
      <header className="hero-header">
        <div className="hero-tag">OUR TEAM</div>
        <h1 className="hero-title">저희 팀을 소개합니다</h1>
        <p className="hero-sub">
          다양한 분야의 전문가들이 모여 함께 만들어가고 있습니다
        </p>
        <div className="hero-divider" />
        <div className="strengths">
          <div className="strength-item">
            <span className="strength-icon">🤝</span>
            <span className="strength-text">긴밀한 협업</span>
          </div>
          <div className="strength-item">
            <span className="strength-icon">🚀</span>
            <span className="strength-text">빠른 실행력</span>
          </div>
          <div className="strength-item">
            <span className="strength-icon">💡</span>
            <span className="strength-text">창의적 문제 해결</span>
          </div>
        </div>
      </header>

      <section className="team-section">
        <p className="section-hint">카드를 클릭하면 상세 정보를 볼 수 있어요</p>
        <div className="grid">
          {members.map((member) => (
            <MemberCard key={member.id} member={member} onClick={setSelected} />
          ))}
        </div>
      </section>

      <Modal member={selected} onClose={() => setSelected(null)} />
    </div>
  )
}

export default App
