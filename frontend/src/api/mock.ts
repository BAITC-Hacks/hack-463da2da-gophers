import type { EmployeeProfile, EmployeeSummary } from './types'

export const mockEmployees: EmployeeSummary[] = [{
  employee_id: 'E0028', full_name: 'Aisultan Nurlybek', department: 'Technology', role: 'Backend Engineer', grade: 'Middle', tenure_months: 18, preferred_language: 'ru', career_goal: { target_role: 'Backend Engineer', target_grade: 'Senior' },
}]

export const mockProfile: EmployeeProfile = {
  employee: mockEmployees[0],
  next_grade: { role: 'Backend Engineer', grade: 'Senior', requirements_met: false },
  skills: [
    { skill_id: 'SK_SYSTEM_DESIGN', name: 'System Design', type: 'hard', current: 2, required: 4, gap: 2, critical: true },
    { skill_id: 'SK_PUBLIC_SPEAKING', name: 'Public Speaking', type: 'soft', current: 2, required: 3, gap: 1, critical: false },
  ],
  history: [],
  available_steps: [],
}
