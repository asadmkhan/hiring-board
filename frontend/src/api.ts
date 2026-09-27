import type { ApplicationPage } from './types'

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(API_URL + path, init)
  } catch {
    throw new ApiError('Could not reach the server.', 0)
  }
  if (!response.ok) {
    throw new ApiError(await errorMessage(response), response.status)
  }
  return (await response.json()) as T
}

// FastAPI puts a string in `detail` for our own errors and a list for validation errors.
async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) return body.detail.map((item: { msg: string }) => item.msg).join(', ')
  } catch {
    // no JSON body, fall through to the generic message
  }
  return `Request failed (${response.status})`
}

export function listApplications(page = 1, pageSize = 20): Promise<ApplicationPage> {
  return request(`/applications?page=${page}&page_size=${pageSize}`)
}
