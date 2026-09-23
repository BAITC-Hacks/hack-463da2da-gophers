import { useEffect, useState, type FormEvent } from 'react'
import { careerQuestApi } from '../api/client'
import type { ActivityFormat, CareerPathsResponse, Language } from '../api/types'

const copy = {
  ru: { heading: 'Выбрать другой путь', intro: 'Сравните два маршрута с учётом вашего времени и формата.', format: 'Формат занятий', any: 'Любой формат', online: 'Онлайн', offline: 'Офлайн', self_paced: 'В своём темпе', hours: 'Часов в неделю', show: 'Показать пути', loading: 'Подбираем пути…', error: 'Не удалось подобрать пути. Попробуйте ещё раз.', empty: 'Для этих условий подходящих шагов нет.', fast: 'Быстрый путь', flexible: 'Гибкий путь', total: 'Всего часов', weeks: 'Примерно недель', readiness: 'Готовность к следующему грейду', why: 'Почему этот путь', limited: 'Гибкий путь учитывает выбранный формат', time: 'Оценка длительности учитывает доступные часы в неделю', default: 'Без ограничения формата', step: 'Шаг', hoursShort: 'ч', changed: 'Ограничение по формату изменило набор шагов гибкого пути', same: 'Выбранный формат подходит обоим путям — набор шагов не изменился', noLimit: 'Без ограничения формата оба пути подбираются по скорости и удобству' },
  kk: { heading: 'Басқа жолды таңдау', intro: 'Уақытыңыз бен оқу форматына сай екі бағытты салыстырыңыз.', format: 'Оқу форматы', any: 'Кез келген формат', online: 'Онлайн', offline: 'Офлайн', self_paced: 'Өз қарқынымен', hours: 'Аптасына сағат', show: 'Жолдарды көрсету', loading: 'Жолдар таңдалуда…', error: 'Жолдарды жүктеу мүмкін болмады. Қайталап көріңіз.', empty: 'Бұл шарттарға сай қадамдар жоқ.', fast: 'Жылдам жол', flexible: 'Икемді жол', total: 'Барлық сағат', weeks: 'Шамамен апта', readiness: 'Келесі деңгейге дайындық', why: 'Неліктен осы жол', limited: 'Икемді жол таңдалған форматты ескереді', time: 'Мерзім апталық бос уақытқа негізделген', default: 'Формат шектеуі жоқ', step: 'Қадам', hoursShort: 'сағ', changed: 'Формат шектеуі икемді жолдағы қадамдарды өзгертті', same: 'Таңдалған формат екі жолға да сай — қадамдар өзгермеді', noLimit: 'Формат шектеуінсіз жолдар жылдамдық пен ыңғайлылық бойынша таңдалады' },
  en: { heading: 'Choose another path', intro: 'Compare two routes for your available time and preferred format.', format: 'Learning format', any: 'Any format', online: 'Online', offline: 'Offline', self_paced: 'Self paced', hours: 'Hours per week', show: 'Show paths', loading: 'Finding paths…', error: 'Could not load paths. Please try again.', empty: 'No eligible steps match these constraints.', fast: 'Fast path', flexible: 'Flexible path', total: 'Total hours', weeks: 'Estimated weeks', readiness: 'Next grade readiness', why: 'Why this path', limited: 'The flexible path honors your selected format', time: 'The time estimate uses your available hours per week', default: 'No format restriction', step: 'Step', hoursShort: 'h', changed: 'The format constraint changed the flexible path steps', same: 'The selected format fits both paths, so the steps stayed the same', noLimit: 'With no format constraint, paths favor speed and convenience' },
} as const

export function CareerTwin({ employeeId, language }: { employeeId: string; language: Language }) {
  const t = copy[language] ?? copy.ru
  const [open, setOpen] = useState(false)
  const [format, setFormat] = useState<ActivityFormat | ''>('')
  const [hours, setHours] = useState('4')
  const [result, setResult] = useState<CareerPathsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => { setResult(null); setError(false); setOpen(false) }, [employeeId])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(false)
    setResult(null)
    try {
      setResult(await careerQuestApi.careerPaths(employeeId, {
        preferred_format: format || null,
        hours_per_week: Number(hours),
      }))
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  return <section className="career-twin" aria-labelledby="career-twin-title">
    <button className="career-twin-toggle" type="button" aria-expanded={open} onClick={() => setOpen(value => !value)}>
      <span>↗</span><strong id="career-twin-title">{t.heading}</strong><span aria-hidden="true">{open ? '−' : '+'}</span>
    </button>
    {open && <div className="career-twin-body">
      <p className="muted">{t.intro}</p>
      <form className="career-twin-form" onSubmit={submit}>
        <label>{t.format}<select value={format} onChange={event => setFormat(event.target.value as ActivityFormat | '')}>
          <option value="">{t.any}</option><option value="online">{t.online}</option><option value="offline">{t.offline}</option><option value="self_paced">{t.self_paced}</option>
        </select></label>
        <label>{t.hours}<input type="number" min="1" max="40" step="1" value={hours} onChange={event => setHours(event.target.value)} required /></label>
        <button className="career-twin-submit" type="submit" disabled={loading}>{loading ? t.loading : t.show}</button>
      </form>
      {loading && <div className="skeleton large" role="status" aria-label={t.loading} />}
      {error && <p role="alert" className="career-twin-alert">{t.error}</p>}
      {result && <>
        {result.paths.length === 0 && <p className="muted">{t.empty}</p>}
        <p className="career-twin-constraint">{format ? (result.paths.length === 2 && result.paths[0].steps.map(step => step.event.event_id).join(",") !== result.paths[1].steps.map(step => step.event.event_id).join(",") ? t.changed : t.same) : t.noLimit}{format ? ` (${t[format]}).` : "."} {t.time}.</p>
        <div className="career-twin-grid">{result.paths.map(path => <article className="career-twin-card" key={path.kind}>
          <div className="career-twin-card-top"><span className="career-twin-kind">{path.kind === 'fast' ? t.fast : t.flexible}</span><span className="career-twin-readiness">{path.readiness.before}% → {path.readiness.after}%</span></div>
          <p className="muted">{t.readiness}</p>
          {path.steps.length ? <>
            <ol className="career-twin-steps">{path.steps.map(step => <li key={step.event.event_id}>
              <span>{t.step} {step.rank}</span><strong>{step.event.title}</strong><small>{t[step.event.format as ActivityFormat] ?? step.event.format} · {step.event.duration_hours} {t.hoursShort}</small>
            </li>)}</ol>
            <div className="career-twin-metrics"><span>{t.total}: <b>{path.total_hours} {t.hoursShort}</b></span>{path.estimated_weeks !== null && <span>{t.weeks}: <b>{path.estimated_weeks}</b></span>}</div>
            <p className="career-twin-reason"><b>{t.why}:</b> {path.kind === 'flexible' && format ? `${t.limited} (${t[format]}). ` : `${t.default}. `}{t.time}.</p>
          </> : <p className="muted">{t.empty}</p>}
        </article>)}</div>
      </>}
    </div>}
  </section>
}
