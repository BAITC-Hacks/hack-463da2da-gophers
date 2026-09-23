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

export type ActivityFormat = 'online' | 'offline' | 'self_paced'

export interface CareerPathRequest {
  preferred_format: ActivityFormat | null
  hours_per_week: number | null
}

export interface CareerPath {
  kind: 'fast' | 'flexible'
  title: string
  status: 'ready' | 'no_eligible_steps'
  constraint_honored: boolean
  reason: string
  steps: Array<{ rank: number; score: number; event: EventSummary }>
  factors: Array<{ type: string; skill_id: string | null; message: string; weight: number }>
  total_hours: number
  estimated_weeks: number | null
  readiness: { before: number; after: number }
}

export interface CareerPathsResponse {
  employee_id: string
  target: { role: string; grade: string } | null
  constraints: CareerPathRequest
  paths: CareerPath[]
  reason?: string
}
