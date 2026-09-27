import { STATUS_LABELS } from './labels'
import type { ApplicationFilters, ApplicationStatus, SortKey } from './types'

export const DEFAULT_FILTERS: ApplicationFilters = {
  status: '',
  country: '',
  job_family: '',
  sort: 'newest',
  page: 1,
}

export const STATUSES = Object.keys(STATUS_LABELS) as ApplicationStatus[]

export const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'newest', label: 'Newest first' },
  { value: 'oldest', label: 'Oldest first' },
  { value: 'highest_score', label: 'Highest match score' },
  { value: 'lowest_score', label: 'Lowest match score' },
]
