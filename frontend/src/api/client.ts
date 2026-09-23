import axios from 'axios'
import { mockEmployees, mockProfile } from './mock'
import type { CareerPathRequest, CareerPathsResponse, EmployeeProfile, EmployeeSummary } from './types'

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000', timeout: 10_000 })
const useMocks = import.meta.env.VITE_USE_MOCKS === 'true'

function employeeHeaders(id: string, token: string) {
  return { 'X-Role': 'employee', 'X-Employee-Id': id, ...(token ? { 'X-Access-Token': token } : {}) }
}

function hrHeaders(token: string) {
  return { 'X-Role': 'hr', ...(token ? { 'X-Access-Token': token } : {}) }
}

export function apiStatus(error: unknown): number | undefined {
  return axios.isAxiosError(error) ? error.response?.status : undefined
}

export type RecommendationResponse = { employee_id: string; generated_at: string; engine: string; recommendations: Array<{ rank: number; event: { event_id: string; title: string; type: string; format: string; duration_hours: number }; factors: Array<{ type: string; message: string; weight: number }>; explanation: { language: string; text: string } }> }
export type CompletionResult = { employee_id: string; event_id: string; skills_updated: Array<{ skill_id: string; before: number; after: number }>; trajectory_updated: boolean; requirements_met: boolean }

export const careerQuestApi = {
  async employees(token = ''): Promise<EmployeeSummary[]> {
    return useMocks ? mockEmployees : (await api.get<EmployeeSummary[]>('/employees', { headers: hrHeaders(token) })).data
  },
  async employee(id: string, token = ''): Promise<EmployeeProfile> {
    return useMocks ? { ...mockProfile, employee: { ...mockProfile.employee, employee_id: id } } : (await api.get<EmployeeProfile>('/employees/' + encodeURIComponent(id), { headers: employeeHeaders(id, token) })).data
  },
  async recommendations(id: string, token = ''): Promise<RecommendationResponse> {
    return (await api.post<RecommendationResponse>('/recommendations/' + encodeURIComponent(id), undefined, { headers: employeeHeaders(id, token) })).data
  },
  async complete(id: string, eventId: string, token = ''): Promise<CompletionResult> {
    return (await api.post<CompletionResult>('/employees/' + encodeURIComponent(id) + '/complete/' + encodeURIComponent(eventId), undefined, { headers: employeeHeaders(id, token) })).data
  },
  async hrDashboard(token = ''): Promise<unknown> {
    return (await api.get('/hr/dashboard', { headers: hrHeaders(token) })).data
  },
  async careerPaths(id: string, constraints: CareerPathRequest, token = ''): Promise<CareerPathsResponse> {
    return (await api.post<CareerPathsResponse>('/employees/' + encodeURIComponent(id) + '/career-paths', constraints, { headers: employeeHeaders(id, token) })).data
  },
}
