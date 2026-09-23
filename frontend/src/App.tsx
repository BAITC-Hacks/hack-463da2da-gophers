import { useCallback, useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import type { Language } from './api/types'
import { labels } from './i18n'
import { useTheme } from './theme/ThemeProvider'
import { EmployeePage, HrPage } from './pages/Placeholders'

function storedLanguage(): Language | null {
  const value = localStorage.getItem('cq-language')
  return value === 'ru' || value === 'kk' || value === 'en' ? value : null
}

export default function App() {
  const { theme, toggleTheme } = useTheme()
  const [language, setLanguage] = useState<Language>(() => storedLanguage() ?? 'ru')
  const [manualLanguage, setManualLanguage] = useState(() => storedLanguage() !== null)
  const t = labels[language]

  useEffect(() => { document.documentElement.lang = language }, [language])
  const usePreferredLanguage = useCallback((preferred: Language) => {
    if (!manualLanguage) setLanguage(preferred)
  }, [manualLanguage])

  function changeLanguage(value: Language) {
    setLanguage(value)
    setManualLanguage(true)
    localStorage.setItem('cq-language', value)
  }

  return <main className="app-shell">
    <header className="app-header">
      <NavLink className="brand" to="/employee"><span className="brand-mark"><img src="/halyk-logo.svg" alt="Halyk Bank" /></span><span>Career Quest <small>for Halyk Bank</small></span></NavLink>
      <div className="bank-context"><span>⌖ {t.city}</span><small>{t.address}</small></div>
      <nav aria-label="Primary navigation">
        <NavLink to="/employee">{t.myPath}</NavLink>
        <NavLink to="/hr">{t.hr}</NavLink>
      </nav>
      <label className="language-control" aria-label={t.language}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.4 3.7 5.4 3.7 9s-1.2 6.6-3.7 9c-2.5-2.4-3.7-5.4-3.7-9S9.5 5.4 12 3Z"/></svg>
        <select value={language} aria-label={t.language} onChange={event => changeLanguage(event.target.value as Language)}>
          <option value="ru">Русский</option><option value="kk">Қазақша</option><option value="en">English</option>
        </select>
      </label>
      <button className="theme-toggle" onClick={toggleTheme} type="button">{theme === 'dark' ? t.light : t.dark}</button>
    </header>
    <Routes>
      <Route path="/employee" element={<EmployeePage language={language} onPreferredLanguage={usePreferredLanguage} />} />
      <Route path="/hr" element={<HrPage language={language} />} />
      <Route path="*" element={<Navigate to="/employee" replace />} />
    </Routes>
  </main>
}