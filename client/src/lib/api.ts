import axios from 'axios'

export type Audience = 'farmer' | 'expert'
export type Language = 'en' | 'sw'

export interface AskRequest {
  question: string
  lat: number
  lon: number
  audience: Audience
  language: Language
  session_id?: string | null
}

export interface AskResponse {
  answer: string
  tools_invoked: string[]
  cache_hit: boolean
  latency_ms: number
  request_id: string
  session_id: string
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
})

export async function askQuestion(payload: AskRequest): Promise<AskResponse> {
  const response = await apiClient.post<AskResponse>('/ask', payload)
  return response.data
}
