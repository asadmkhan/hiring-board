import { render, screen } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import ApplicationList from './ApplicationList'
import { listApplications } from './api'
import type { ApplicationPage } from './types'

vi.mock('./api', () => ({ listApplications: vi.fn() }))
const mockedList = vi.mocked(listApplications)

const page: ApplicationPage = {
  items: [
    {
      application_id: 'A1',
      created_at: '2026-03-01T09:00:00',
      source: 'job_board',
      match_score: 0.5,
      match_band: 'medium',
      status: 'new',
      status_updated_at: null,
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
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
}

beforeEach(() => {
  mockedList.mockReset()
})

it('shows the loading text first', () => {
  mockedList.mockReturnValue(new Promise(() => {}))

  render(<ApplicationList />)

  expect(screen.getByText('Loading applications...')).toBeInTheDocument()
})

it('shows one row per application', async () => {
  mockedList.mockResolvedValue(page)

  render(<ApplicationList />)

  expect(await screen.findByText('Anna Adler')).toBeInTheDocument()
  expect(screen.getByText('Warehouse Associate')).toBeInTheDocument()
  expect(screen.getByText('2026-03-01 09:00')).toBeInTheDocument()
  expect(screen.getByText('1 applications')).toBeInTheDocument()
})

it('shows the empty message', async () => {
  mockedList.mockResolvedValue({ ...page, items: [], total: 0 })

  render(<ApplicationList />)

  expect(await screen.findByText('No applications found.')).toBeInTheDocument()
})

it('shows the error message with a retry button', async () => {
  mockedList.mockRejectedValue(new Error('Could not reach the server.'))

  render(<ApplicationList />)

  expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach the server.')
  expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
})
