import axios from 'axios'
import { mockEmployees, mockProfile } from './mock'
import type { EmployeeProfile, EmployeeSummary } from './types'

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000', timeout: 10_000 })
const useMocks = import.meta.env.VITE_USE_MOCKS === 'true'
export type RecommendationResponse = { employee_id: string; generated_at: string; engine: string; recommendations: Array<{ rank:number; event:{event_id:string;title:string;type:string;format:string;duration_hours:number}; factors:Array<{type:string;message:string;weight:number}>; explanation:{language:string;text:string} }> }
export type CompletionResult = { employee_id:string; event_id:string; skills_updated:Array<{skill_id:string;before:number;after:number}>; trajectory_updated:boolean; requirements_met:boolean }
export const careerQuestApi = {
  async employees(): Promise<EmployeeSummary[]> { return useMocks ? mockEmployees : (await api.get<EmployeeSummary[]>('/employees')).data },
  async employee(id: string): Promise<EmployeeProfile> { return useMocks ? { ...mockProfile, employee: { ...mockProfile.employee, employee_id: id } } : (await api.get<EmployeeProfile>(`/employees/${id}`)).data },
  async recommendations(id: string): Promise<RecommendationResponse> { return (await api.post<RecommendationResponse>(`/recommendations/${id}`)).data },
  async complete(id: string, eventId: string): Promise<CompletionResult> { return (await api.post<CompletionResult>(`/employees/${id}/complete/${eventId}`)).data },
  async hrDashboard(): Promise<unknown> { return (await api.get('/hr/dashboard', { headers: { 'X-Role': 'hr' } })).data },
}
