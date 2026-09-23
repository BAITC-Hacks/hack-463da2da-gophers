import axios from 'axios'
import { mockEmployees, mockProfile } from './mock'
import type { EmployeeProfile, EmployeeSummary } from './types'

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000', timeout: 10_000 })
const useMocks = import.meta.env.VITE_USE_MOCKS !== 'false'

export const careerQuestApi = {
  async employees(): Promise<EmployeeSummary[]> {
    return useMocks ? mockEmployees : (await api.get<EmployeeSummary[]>('/employees')).data
  },
  async employee(id: string): Promise<EmployeeProfile> {
    return useMocks ? { ...mockProfile, employee: { ...mockProfile.employee, employee_id: id } } : (await api.get<EmployeeProfile>(`/employees/${id}`)).data
  },
}
