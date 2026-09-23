import { useEffect, useState } from 'react'
import { careerQuestApi } from '../api/client'
import type { EmployeeProfile } from '../api/types'
import { Recommendations } from './Recommendations'
import { labels } from '../i18n'

function Radar({ skills }: { skills: EmployeeProfile['skills'] }) {
  const point = (i: number, level: number) => { const a = (Math.PI * 2 * i) / skills.length - Math.PI / 2; const r = 76 * level / 5; return `${110 + Math.cos(a) * r},${110 + Math.sin(a) * r}` }
  return <svg className="radar" viewBox="0 0 220 220" role="img" aria-label="Текущие и требуемые навыки">{[1,2,3,4,5].map(n => <polygon key={n} className="radar-grid" points={skills.map((_, i) => point(i,n)).join(' ')} />)}<polygon className="radar-target" points={skills.map((s,i) => point(i,s.required)).join(' ')} /><polygon className="radar-current" points={skills.map((s,i) => point(i,s.current)).join(' ')} />{skills.map((s,i) => <text key={s.skill_id} className={s.critical ? 'critical-text' : ''} x={point(i,6).split(',')[0]} y={point(i,6).split(',')[1]}>{s.name}</text>)}</svg>
}
export function EmployeePage() {
 const [profile, setProfile] = useState<EmployeeProfile>(); const reloadProfile = () => { void careerQuestApi.employee('E0028').then(setProfile) }; useEffect(() => { reloadProfile() }, [])
 if (!profile) return <section className="page"><div className="skeleton heading" /><div className="skeleton large" /></section>
 const { employee, next_grade, skills, history } = profile
 return <section className="page"><p className="eyebrow">{labels[employee.preferred_language].path}</p><h1>{employee.full_name}</h1><div className="profile-grid"><article className="panel"><h2>{employee.role} · {employee.grade}</h2><p>{employee.department} · {employee.tenure_months} месяцев в компании</p><p>Цель: <b>{employee.career_goal?.target_role} {employee.career_goal?.target_grade}</b></p><p className={next_grade.requirements_met ? 'success' : 'warning'}>Траектория: {next_grade.grade}</p></article><article className="panel chart"><Radar skills={skills}/><small>Синий — текущий уровень, золотой контур — требуемый.</small></article></div><h2>{labels[employee.preferred_language].skills}</h2><div className="skills">{skills.map(s => <article className="skill" key={s.skill_id}><div><b>{s.name}</b>{s.critical && <em>Критичный</em>}<small>{s.current}/5 сейчас · требуется {s.required}/5</small></div><div className="meter"><i style={{width:`${s.current*20}%`}}/><strong style={{left:`${s.required*20}%`}}/></div></article>)}</div><h2>Как закрыть разрыв</h2><div className="skills">{profile.available_steps.map(step => <article className="skill" key={step.event_id}><b>{step.title}</b><small>{step.format} · {step.duration_hours} ч.</small></article>)}</div><Recommendations onCompleted={reloadProfile} /><h2>{labels[employee.preferred_language].history}</h2>{history.length ? <ul>{history.map(r=><li key={r.record_id}>{r.title} — {r.status}</li>)}</ul> : <p className="muted">Пока нет завершённых активностей.</p>}</section>
}
export function HrPage() {
 const [data,setData]=useState<any>(); const [error,setError]=useState(''); useEffect(()=>{careerQuestApi.hrDashboard().then(setData).catch(()=>setError('Не удалось загрузить HR-агрегаты.'))},[])
 if(error)return <section className="page"><h1>HR-дашборд</h1><p className="muted">{error}</p></section>
 if(!data)return <section className="page"><h1>HR-дашборд</h1><div className="skeleton large"/></section>
 return <section className="page"><p className="eyebrow">Только для HR</p><h1>HR-дашборд</h1><div className="dashboard"><article className="panel"><h2>Проседающие навыки</h2>{data.weak_skills?.map((s:any)=><p key={s.skill_id}><b>{s.name}</b> · средний разрыв {s.avg_gap}</p>)}</article><article className="panel"><h2>Без рекомендации</h2><p>{data.employees_without_recommendation?.length ?? 0} сотрудников требуют внимания</p><small>Личная вовлечённость не раскрывается.</small></article><article className="panel"><h2>Участие в активностях</h2>{data.activity_engagement?.map((a:any)=><p key={a.event_id}>{a.title}: <b>{Math.round(a.completion_rate*100)}%</b></p>)}</article></div></section>
}




