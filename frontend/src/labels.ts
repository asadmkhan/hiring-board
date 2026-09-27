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
