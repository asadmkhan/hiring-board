export type ApplicationStatus = 'new' | 'in_review' | 'shortlisted' | 'rejected' | 'hired'

export interface ApplicationCandidate {
  candidate_id: string
  full_name: string
  email: string
  country: string
  city: string
  years_experience: number
  preferred_job_family: string
}

export interface ApplicationJob {
  job_id: string
  title: string
  job_family: string
  seniority: string
  country: string
  city: string
  created_at: string
}

export interface ApplicationListItem {
  application_id: string
  created_at: string
  source: string
  match_score: number
  match_band: string
  status: ApplicationStatus
  status_updated_at: string | null
  candidate: ApplicationCandidate
  job: ApplicationJob
}

export interface ApplicationPage {
  items: ApplicationListItem[]
  total: number
  page: number
  page_size: number
}

export type SortKey = 'newest' | 'oldest' | 'highest_score' | 'lowest_score'

// Empty string means "all" for the three filters.
export interface ApplicationFilters {
  status: ApplicationStatus | ''
  country: string
  job_family: string
  q: string
  sort: SortKey
  page: number
}

export interface FilterOptions {
  countries: string[]
  job_families: string[]
}

export interface ApplicationLlmScore {
  provider: string
  model: string
  score: number
  reason: string
  scored_at: string
}

export interface ApplicationDetail extends ApplicationListItem {
  note: string | null
  llm_scores: ApplicationLlmScore[]
}

export interface ApplicationUpdate {
  status?: ApplicationStatus
  note?: string | null
}

export interface LlmProvider {
  id: string
  label: string
  model: string
}

export interface LlmScoreResponse extends ApplicationLlmScore {
  cached: boolean
}
