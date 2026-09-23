export type Language = 'ru' | 'kk' | 'en'

export interface EmployeeSummary {
  employee_id: string
  full_name: string
  department: string
  role: string
  grade: string
  tenure_months: number
  preferred_language: Language
  career_goal: { target_role: string; target_grade: string } | null
}

export interface EmployeeProfile {
  employee: EmployeeSummary
  next_grade: { role: string; grade: string; requirements_met: boolean }
  skills: Array<{ skill_id: string; name: string; type: 'hard' | 'soft'; current: number; required: number; gap: number; critical: boolean }>
  history: Array<{ record_id: string; event_id: string; title: string; date: string; due_date: string | null; status: string; completion_pct: number; score: number | null; feedback_rating: number | null; assigned_by: string }>
  available_steps: EventSummary[]
}

export interface EventSummary { event_id: string; title: string; type: string; format: string; duration_hours: number; mandatory: boolean }
