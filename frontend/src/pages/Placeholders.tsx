import { useCallback, useEffect, useState } from 'react'
import { careerQuestApi } from '../api/client'
import type { EmployeeProfile, EmployeeSummary, Language } from '../api/types'
import { formatLabels, labels, statusLabels } from '../i18n'
import { CareerTwin } from './CareerTwin'
import { Recommendations } from './Recommendations'

function Radar({ skills, language }: { skills: EmployeeProfile['skills']; language: Language }) {
  const point = (index: number, level: number) => {
    const angle = Math.PI * 2 * index / skills.length - Math.PI / 2
    const radius = 76 * level / 5
    return `${110 + Math.cos(angle) * radius},${110 + Math.sin(angle) * radius}`
  }
  return <svg className="radar" viewBox="0 0 220 220" role="img" aria-label={labels[language].radar}>
    {[1, 2, 3, 4, 5].map(level => <polygon key={level} className="radar-grid" points={skills.map((_, index) => point(index, level)).join(' ')} />)}
    <polygon className="radar-target" points={skills.map((skill, index) => point(index, skill.required)).join(' ')} />
    <polygon className="radar-current" points={skills.map((skill, index) => point(index, skill.current)).join(' ')} />
    {skills.map((skill, index) => <text key={skill.skill_id} className={skill.critical ? 'critical-text' : ''} x={point(index, 6).split(',')[0]} y={point(index, 6).split(',')[1]}>{skill.name}</text>)}
  </svg>
}

export function EmployeePage({ language, onPreferredLanguage }: { language: Language; onPreferredLanguage: (language: Language) => void }) {
  const [employeeId, setEmployeeId] = useState('E0028')
  const [employees, setEmployees] = useState<EmployeeSummary[]>([])
  const [profile, setProfile] = useState<EmployeeProfile>()
  const t = labels[language]
  const reloadProfile = useCallback(() => careerQuestApi.employee(employeeId).then(setProfile), [employeeId])

  useEffect(() => { setProfile(undefined); void reloadProfile() }, [reloadProfile])
  useEffect(() => { void careerQuestApi.employees().then(setEmployees) }, [])
  useEffect(() => { if (profile) onPreferredLanguage(profile.employee.preferred_language) }, [profile?.employee.preferred_language, onPreferredLanguage])

  if (!profile) return <section className="page"><div className="skeleton heading" /><div className="skeleton large" /></section>

  const { employee, next_grade, skills, history } = profile
  const sortedHistory = [...history].sort((a, b) => b.date.localeCompare(a.date))

  return <section className="page">
    <p className="eyebrow">{t.path}</p>
    <h1>{employee.full_name}</h1>
    <label className="employee-selector">{t.selectEmployee}
      <select value={employeeId} onChange={event => setEmployeeId(event.target.value)}>
        {employees.map(item => <option key={item.employee_id} value={item.employee_id}>{item.full_name}</option>)}
      </select>
    </label>
    <div className="profile-grid">
      <article className="panel">
        <h2>{employee.role} · {employee.grade}</h2>
        <p>{employee.department} · {employee.tenure_months} {t.tenure}</p>
        <p>{t.goal}: <b>{employee.career_goal ? `${employee.career_goal.target_role} ${employee.career_goal.target_grade}` : `${next_grade.role} ${next_grade.grade}`}</b></p>
        <p className={next_grade.requirements_met ? 'success' : 'warning'}>{t.trajectory}: {next_grade.grade}</p>
      </article>
      <article className="panel chart"><Radar skills={skills} language={language} /><small>{t.radar}</small></article>
    </div>
    <Recommendations employeeId={employeeId} language={language} onCompleted={reloadProfile} />
    <CareerTwin employeeId={employeeId} language={language} />
    <h2>{t.skills}</h2>
    <div className="skills">{skills.map(skill => <article className="skill" key={skill.skill_id}>
      <div><b>{skill.name}</b>{skill.critical && <em>{t.critical}</em>}<small>{skill.current}/5 {t.current} · {t.required} {skill.required}/5</small></div>
      <div className="meter"><i style={{ width: `${skill.current * 20}%` }} /><strong style={{ left: `${skill.required * 20}%` }} /></div>
    </article>)}</div>
    <h2>{t.closeGap}</h2>
    <div className="skills">{profile.available_steps.map(step => <article className="skill" key={step.event_id}>
      <b>{step.title}</b><small>{formatLabels[language][step.format] ?? step.format} · {step.duration_hours} {t.hoursShort}</small>
    </article>)}</div>
    <section className="history-section" aria-labelledby="history-title">
      <div className="history-heading">
        <span className="history-heading-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M7 3v4M17 3v4M3 10h18M8 15h3"/></svg></span>
        <div><h2 id="history-title">{t.history}</h2><p>{t.historyIntro}</p></div>
        <span className="history-count" aria-label={`${history.length}`}>{history.length}</span>
      </div>
      {history.length ? <ol className="history-list">{sortedHistory.map(record => <li key={record.record_id} className="history-item">
        <span className="history-date">{new Intl.DateTimeFormat(language, { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(record.date))}</span>
        <strong>{record.title}</strong>
        <span className={`history-status status-${record.status}`}>{statusLabels[language][record.status] ?? record.status}</span>
      </li>)}</ol> : <p className="muted">{t.noHistory}</p>}
    </section>
  </section>
}

export function HrPage({ language }: { language: Language }) {
  const [data, setData] = useState<any>()
  const [error, setError] = useState(false)
  const t = labels[language]
  useEffect(() => { void careerQuestApi.hrDashboard().then(setData).catch(() => setError(true)) }, [])
  if (error) return <section className="page"><h1>{t.hr}</h1><p className="muted">{t.hrError}</p></section>
  if (!data) return <section className="page"><h1>{t.hr}</h1><div className="skeleton large" /></section>
  return <section className="page">
    <p className="eyebrow">{t.hrOnly}</p><h1>{t.hr}</h1>
    <div className="dashboard">
      <article className="panel"><h2>{t.weakSkills}</h2>{data.weak_skills?.map((skill: any) => <p key={skill.skill_id}><b>{skill.name}</b> · {t.avgGap} {skill.avg_gap}</p>)}</article>
      <article className="panel"><h2>{t.withoutRec}</h2><p>{data.employees_without_recommendation?.length ?? 0} {t.employees}</p><small>{t.privacy}</small></article>
      <article className="panel"><h2>{t.engagement}</h2>{data.activity_engagement?.map((activity: any) => <p key={activity.event_id}>{activity.title}: <b>{Math.round(activity.completion_rate * 100)}%</b></p>)}</article>
    </div>
  </section>
}