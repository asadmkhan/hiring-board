import type {
  ApplicationDetail,
  ApplicationFilters,
  ApplicationPage,
  ApplicationUpdate,
  FilterOptions,
  SortKey,
} from './types'

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong.'
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
  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError('The server sent an unreadable response.', response.status)
  }
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

const PAGE_SIZE = 20

const SORT_PARAMS: Record<SortKey, { sort: string; order: string }> = {
  newest: { sort: 'created_at', order: 'desc' },
  oldest: { sort: 'created_at', order: 'asc' },
  highest_score: { sort: 'match_score', order: 'desc' },
  lowest_score: { sort: 'match_score', order: 'asc' },
}

export function listApplications(filters: ApplicationFilters): Promise<ApplicationPage> {
  const params = new URLSearchParams({
    ...SORT_PARAMS[filters.sort],
    page: String(filters.page),
    page_size: String(PAGE_SIZE),
  })
  if (filters.status) params.set('status', filters.status)
  if (filters.country) params.set('country', filters.country)
  if (filters.job_family) params.set('job_family', filters.job_family)
  return request(`/applications?${params}`)
}

export function getFilterOptions(): Promise<FilterOptions> {
  return request('/filter-options')
}

export function getApplication(id: string): Promise<ApplicationDetail> {
  return request(`/applications/${encodeURIComponent(id)}`)
}

export function updateApplication(id: string, changes: ApplicationUpdate): Promise<ApplicationDetail> {
  return request(`/applications/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(changes),
  })
}
