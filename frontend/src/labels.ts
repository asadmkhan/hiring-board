import type { ApplicationStatus } from './types'

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  new: 'New',
  in_review: 'In review',
  shortlisted: 'Shortlisted',
  rejected: 'Rejected',
  hired: 'Hired',
}

const COUNTRY_LABELS: Record<string, string> = {
  DE: 'Germany',
  AT: 'Austria',
}

// Unknown codes fall back to the code itself, never to blank.
export function countryLabel(code: string): string {
  return COUNTRY_LABELS[code] ?? code
}

const BAND_LABELS: Record<string, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
}

export function bandLabel(code: string): string {
  return BAND_LABELS[code] ?? code
}

const SOURCE_LABELS: Record<string, string> = {
  job_board: 'Job board',
  career_site: 'Career site',
  referral: 'Referral',
}

export function sourceLabel(code: string): string {
  return SOURCE_LABELS[code] ?? code
}

const SENIORITY_LABELS: Record<string, string> = {
  junior: 'Junior',
  mid: 'Mid-level',
  senior: 'Senior',
}

export function seniorityLabel(code: string): string {
  return SENIORITY_LABELS[code] ?? code
}

const PROVIDER_LABELS: Record<string, string> = {
  mock: 'Mock',
  claude: 'Claude',
  openai: 'OpenAI',
  ollama: 'Ollama',
}

export function providerLabel(code: string): string {
  return PROVIDER_LABELS[code] ?? code
}
