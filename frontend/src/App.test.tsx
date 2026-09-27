import { fireEvent, render, screen, within } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import App from './App'
import { getApplication, getFilterOptions, listApplications, updateApplication } from './api'
import type { ApplicationDetail, ApplicationFilters } from './types'

vi.mock('./api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./api')>()),
  listApplications: vi.fn(),
  getFilterOptions: vi.fn(),
  getApplication: vi.fn(),
  updateApplication: vi.fn(),
}))

const detail: ApplicationDetail = {
  application_id: 'A1',
  created_at: '2026-03-01T09:00:00',
  source: 'job_board',
  match_score: 0.5,
  match_band: 'medium',
  status: 'new',
  status_updated_at: null,
  note: null,
  llm_scores: [],
  candidate: {
    candidate_id: 'C1',
    full_name: 'Anna Adler',
    email: 'anna@example.com',
    country: 'DE',
    city: 'Hamburg',
    years_experience: 3,
    preferred_job_family: 'Logistics',
  },
  job: {
    job_id: 'J1',
    title: 'Warehouse Associate',
    job_family: 'Logistics',
    seniority: 'junior',
    country: 'DE',
    city: 'Hamburg',
    created_at: '2026-01-01T09:00:00',
  },
}

beforeEach(() => {
  vi.mocked(getFilterOptions).mockResolvedValue({ countries: ['DE'], job_families: ['Logistics'] })
  vi.mocked(listApplications).mockImplementation((filters: ApplicationFilters) =>
    Promise.resolve({ items: [detail], total: 1, page: filters.page, page_size: 20 }),
  )
  vi.mocked(getApplication).mockResolvedValue(detail)
  vi.mocked(updateApplication).mockResolvedValue({ ...detail, status: 'hired', status_updated_at: '2026-09-27T10:00:00' })
})

it('opens the panel from a row, saves, and reloads the list', async () => {
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Anna Adler' }))

  expect(await screen.findByRole('heading', { name: 'Anna Adler' })).toBeInTheDocument()
  const listCallsBefore = vi.mocked(listApplications).mock.calls.length

  const panel = screen.getByRole('complementary', { name: 'Application details' })
  fireEvent.change(within(panel).getByLabelText('Status'), { target: { value: 'hired' } })
  fireEvent.click(within(panel).getByRole('button', { name: 'Save' }))

  expect(await screen.findByText('Saved.')).toBeInTheDocument()
  expect(vi.mocked(listApplications).mock.calls.length).toBe(listCallsBefore + 1)

  fireEvent.click(screen.getByRole('button', { name: 'Close' }))
  expect(screen.queryByRole('heading', { name: 'Anna Adler' })).not.toBeInTheDocument()
})
