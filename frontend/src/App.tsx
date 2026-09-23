import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { useTheme } from './theme/ThemeProvider'
import { EmployeePage, HrPage } from './pages/Placeholders'

export default function App() {
  const { theme, toggleTheme } = useTheme()

  return (
    <main className="app-shell">
      <header className="app-header">
        <NavLink className="brand" to="/employee"><span className="brand-mark">◈</span><span>Career Quest <small>for Halyk Bank</small></span></NavLink>
        <div className="bank-context"><span>⌖ Алматы</span><small>пр. Аль-Фараби, 40</small></div><nav aria-label="Основная навигация">
          <NavLink to="/employee">Мой путь</NavLink>
          <NavLink to="/hr">HR-дашборд</NavLink>
        </nav>
        <button className="theme-toggle" onClick={toggleTheme} type="button">
          {theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
        </button>
      </header>
      <Routes>
        <Route path="/employee" element={<EmployeePage />} />
        <Route path="/hr" element={<HrPage />} />
        <Route path="*" element={<Navigate to="/employee" replace />} />
      </Routes>
    </main>
  )
}

