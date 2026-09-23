import { useEffect, useState } from 'react'
import { careerQuestApi, type RecommendationResponse } from '../api/client'
import type { Language } from '../api/types'
import { labels } from '../i18n'

export function Recommendations({ employeeId, token, language, onCompleted }: { employeeId: string; token: string; language: Language; onCompleted: () => void }) {
  const [data, setData] = useState<RecommendationResponse>()
  const [error, setError] = useState(false)
  const [pending, setPending] = useState<string | null>(null)
  const t = labels[language]

  useEffect(() => {
    let active = true
    setData(undefined)
    setError(false)
    void careerQuestApi.recommendations(employeeId, token)
      .then(result => { if (active) setData(result) })
      .catch(() => { if (active) setError(true) })
    return () => { active = false }
  }, [employeeId, token])

  async function complete(eventId: string) {
    setPending(eventId)
    setError(false)
    try {
      await careerQuestApi.complete(employeeId, eventId, token)
      onCompleted()
      setData(await careerQuestApi.recommendations(employeeId, token))
    } catch {
      setError(true)
    } finally {
      setPending(null)
    }
  }

  return <section className="recommendations-section">
    <h2>{t.recommendations}</h2>
    {error && <p role="alert" className="muted">{t.recError}</p>}
    {!data && !error && <div className="skeleton large" role="status" />}
    {data?.recommendations.length === 0 && <p className="muted">{t.recEmpty}</p>}
    {data?.recommendations.map(item => <article className="recommendation" key={item.event.event_id}>
      <h3>#{item.rank} · {item.event.title}</h3>
      <p>{item.explanation?.text}</p>
      <ul>{item.factors.map((factor, index) => <li key={`${factor.type}-${index}`}>{factor.message}</li>)}</ul>
      <button type="button" disabled={pending !== null} onClick={() => void complete(item.event.event_id)}>
        {pending === item.event.event_id ? t.completing : t.complete}
      </button>
    </article>)}
  </section>
}
