import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { ApiError, getApplication, updateApplication } from '../api'
import type { ApplicationDetail as Detail } from '../types'
import ApplicationDetail from './ApplicationDetail'

vi.mock('../api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api')>()),
  getApplication: vi.fn(),
  updateApplication: vi.fn(),
}))
const mockedGet = vi.mocked(getApplication)
const mockedUpdate = vi.mocked(updateApplication)

const detail: Detail = {
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

const onChanged = vi.fn()
const onClose = vi.fn()

function renderDetail() {
  return render(<ApplicationDetail id="A1" onChanged={onChanged} onClose={onClose} />)
}

beforeEach(() => {
  mockedGet.mockReset()
  mockedUpdate.mockReset()
  onChanged.mockReset()
  onClose.mockReset()
})

it('shows the loading text first', () => {
  mockedGet.mockReturnValue(new Promise(() => {}))

  renderDetail()

  expect(screen.getByRole('status')).toHaveTextContent('Loading application...')
})

it('shows the application, candidate and job', async () => {
  mockedGet.mockResolvedValue(detail)

  renderDetail()

  expect(await screen.findByRole('heading', { name: 'Anna Adler' })).toBeInTheDocument()
  expect(mockedGet).toHaveBeenCalledWith('A1')
  expect(screen.getByText('anna@example.com')).toBeInTheDocument()
  expect(screen.getByText('Warehouse Associate')).toBeInTheDocument()
  expect(screen.getByText('0.5 (Medium)')).toBeInTheDocument()
  expect(screen.getByText('Logistics, Junior')).toBeInTheDocument()
  expect(screen.getByText('Job board')).toBeInTheDocument()
  expect(screen.getByText('never')).toBeInTheDocument()
  expect(screen.getByText('No AI score yet.')).toBeInTheDocument()
  expect(screen.getByLabelText('Status')).toHaveValue('new')
  expect(screen.getByRole('button', { name: 'Save' })).toHaveAttribute('aria-disabled', 'true')
})

it('lists stored AI scores', async () => {
  mockedGet.mockResolvedValue({
    ...detail,
    llm_scores: [{ provider: 'mock', model: 'mock-rules-v1', score: 85, reason: 'Mock score.', scored_at: '2026-09-26T23:32:14' }],
  })

  renderDetail()

  expect(await screen.findByText(/Mock: 85 \/ 100\. Mock score\./)).toBeInTheDocument()
})

it('shows a load error with retry and close', async () => {
  mockedGet.mockRejectedValueOnce(new ApiError('Application not found', 404)).mockResolvedValue(detail)

  renderDetail()

  expect(await screen.findByRole('alert')).toHaveTextContent('Application not found')
  fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
  expect(await screen.findByRole('heading', { name: 'Anna Adler' })).toBeInTheDocument()
})

it('saves only the changed fields and shows what came back', async () => {
  mockedGet.mockResolvedValue(detail)
  mockedUpdate.mockResolvedValue({ ...detail, status: 'shortlisted', status_updated_at: '2026-09-27T10:00:00' })
  renderDetail()
  await screen.findByRole('heading', { name: 'Anna Adler' })

  fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'shortlisted' } })
  expect(screen.getByRole('button', { name: 'Save' })).toHaveAttribute('aria-disabled', 'false')
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))

  expect(mockedUpdate).toHaveBeenCalledWith('A1', { status: 'shortlisted' })
  expect(await screen.findByText('Saved.')).toBeInTheDocument()
  expect(screen.getByText('Shortlisted', { selector: 'div' })).toBeInTheDocument()
  expect(screen.getByText('2026-09-27 10:00')).toBeInTheDocument()
  expect(onChanged).toHaveBeenCalledTimes(1)
  expect(screen.getByRole('button', { name: 'Save' })).toHaveAttribute('aria-disabled', 'true')
})

it('sends null when the note box is emptied', async () => {
  mockedGet.mockResolvedValue({ ...detail, note: 'Call back' })
  mockedUpdate.mockResolvedValue({ ...detail, note: null })
  renderDetail()
  await screen.findByRole('heading', { name: 'Anna Adler' })

  fireEvent.change(screen.getByLabelText('Note'), { target: { value: '   ' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))

  expect(mockedUpdate).toHaveBeenCalledWith('A1', { note: null })
  expect(await screen.findByText('Saved.')).toBeInTheDocument()
})

it('keeps the edits and shows the message when saving fails', async () => {
  mockedGet.mockResolvedValue(detail)
  mockedUpdate.mockRejectedValue(new ApiError('Could not reach the server.', 0))
  renderDetail()
  await screen.findByRole('heading', { name: 'Anna Adler' })

  fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'rejected' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))

  expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach the server.')
  expect(screen.getByLabelText('Status')).toHaveValue('rejected')
  expect(screen.getByRole('button', { name: 'Save' })).toHaveAttribute('aria-disabled', 'false')
  expect(onChanged).not.toHaveBeenCalled()
})

it('closes on the close button', async () => {
  mockedGet.mockResolvedValue(detail)
  renderDetail()
  await screen.findByRole('heading', { name: 'Anna Adler' })

  fireEvent.click(screen.getByRole('button', { name: 'Close' }))

  expect(onClose).toHaveBeenCalledTimes(1)
})

it('locks the form while saving', async () => {
  mockedGet.mockResolvedValue(detail)
  mockedUpdate.mockReturnValue(new Promise(() => {}))
  renderDetail()
  await screen.findByRole('heading', { name: 'Anna Adler' })

  fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'hired' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))

  expect(screen.getByRole('button', { name: 'Saving...' })).toHaveAttribute('aria-disabled', 'true')
  expect(screen.getByLabelText('Status')).toBeDisabled()
  expect(screen.getByLabelText('Note')).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Close' })).toBeDisabled()
})

it('clears the saved message when the user edits again', async () => {
  mockedGet.mockResolvedValue(detail)
  mockedUpdate.mockResolvedValue({ ...detail, note: 'Hi' })
  renderDetail()
  await screen.findByRole('heading', { name: 'Anna Adler' })
  fireEvent.change(screen.getByLabelText('Note'), { target: { value: 'Hi' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))
  await screen.findByText('Saved.')
  expect(screen.getByLabelText('Note')).toHaveValue('Hi')

  fireEvent.change(screen.getByLabelText('Note'), { target: { value: 'Hi again' } })

  expect(screen.queryByText('Saved.')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Save' })).toHaveAttribute('aria-disabled', 'false')
})

it('closes from the load error state', async () => {
  mockedGet.mockRejectedValue(new ApiError('Application not found', 404))
  renderDetail()
  await screen.findByRole('alert')

  fireEvent.click(screen.getByRole('button', { name: 'Close' }))

  expect(onClose).toHaveBeenCalledTimes(1)
})
