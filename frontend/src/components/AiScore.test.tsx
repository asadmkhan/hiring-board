import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { ApiError, getLlmProviders, scoreApplication } from '../api'
import type { ApplicationLlmScore } from '../types'
import AiScore from './AiScore'

vi.mock('../api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api')>()),
  getLlmProviders: vi.fn(),
  scoreApplication: vi.fn(),
}))
const mockedProviders = vi.mocked(getLlmProviders)
const mockedScore = vi.mocked(scoreApplication)

const providers = [
  { id: 'mock', label: 'Mock (no model call)', model: 'mock-rules-v1' },
  { id: 'claude', label: 'Claude', model: 'claude-haiku-4-5' },
]

const stored: ApplicationLlmScore = {
  provider: 'mock',
  model: 'mock-rules-v1',
  score: 85,
  reason: 'Mock score: same country.',
  scored_at: '2026-09-26T23:32:14',
}

function renderWidget(storedScores: ApplicationLlmScore[] = []) {
  return render(<AiScore applicationId="A1" matchScore={0.83} matchBand="high" storedScores={storedScores} />)
}

beforeEach(() => {
  mockedProviders.mockReset()
  mockedScore.mockReset()
  mockedProviders.mockResolvedValue(providers)
})

it('shows the rule-based score and the stored AI scores', async () => {
  renderWidget([stored])

  expect(screen.getByText('0.83 (High)')).toBeInTheDocument()
  expect(screen.getByText('Rule score (0-1)')).toBeInTheDocument()
  expect(screen.getByText(/Mock: 85 \/ 100\. Mock score: same country\./)).toBeInTheDocument()
  expect(await screen.findByRole('option', { name: 'Claude (claude-haiku-4-5)' })).toBeInTheDocument()
})

it('says when there is no AI score yet', async () => {
  renderWidget()

  expect(screen.getByText('No AI score yet.')).toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent('Loading providers...')
  await screen.findByRole('option', { name: 'Claude (claude-haiku-4-5)' })
  expect(screen.getByRole('status')).toHaveTextContent('')
})

it('says when no provider is set up', async () => {
  mockedProviders.mockResolvedValue([])
  renderWidget()

  expect(await screen.findByText('No scoring providers are set up on this server.')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Get AI score' })).toHaveAttribute('aria-disabled', 'true')
})

it('stores a new score and shows it', async () => {
  mockedScore.mockResolvedValue({ ...stored, provider: 'claude', model: 'claude-haiku-4-5', score: 72, reason: 'Good fit.', cached: false })
  renderWidget([stored])
  await screen.findByRole('option', { name: 'Claude (claude-haiku-4-5)' })

  fireEvent.change(screen.getByLabelText('Provider'), { target: { value: 'claude' } })
  fireEvent.click(screen.getByRole('button', { name: 'Get AI score' }))

  expect(mockedScore).toHaveBeenCalledWith('A1', 'claude')
  expect(await screen.findByText(/Claude: 72 \/ 100\. Good fit\./)).toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent('New Claude score stored.')

  fireEvent.change(screen.getByLabelText('Provider'), { target: { value: 'mock' } })
  expect(screen.getByRole('status')).toHaveTextContent('')
  expect(screen.getAllByRole('listitem')).toHaveLength(2)
})

it('says when a stored score was reused and does not add a duplicate line', async () => {
  mockedScore.mockResolvedValue({ ...stored, cached: true })
  renderWidget([stored])
  await screen.findByRole('option', { name: 'Mock (no model call) (mock-rules-v1)' })

  fireEvent.click(screen.getByRole('button', { name: 'Get AI score' }))

  expect(await screen.findByText('Stored Mock (no model call) score reused, the model was not called again.')).toBeInTheDocument()
  expect(screen.getAllByRole('listitem')).toHaveLength(1)
})

it('says the score is unavailable when the call fails and shows no number', async () => {
  mockedScore.mockRejectedValue(new ApiError('Could not reach Claude.', 502))
  renderWidget()
  await screen.findByRole('option', { name: 'Claude (claude-haiku-4-5)' })

  fireEvent.click(screen.getByRole('button', { name: 'Get AI score' }))

  expect(await screen.findByRole('alert')).toHaveTextContent('AI score unavailable: Could not reach Claude.')
  expect(screen.getByText('No AI score yet.')).toBeInTheDocument()
  expect(screen.queryByRole('listitem')).not.toBeInTheDocument()
})

it('locks the form while scoring and ignores a second click', async () => {
  mockedScore.mockReturnValue(new Promise(() => {}))
  renderWidget()
  await screen.findByRole('option', { name: 'Claude (claude-haiku-4-5)' })

  fireEvent.click(screen.getByRole('button', { name: 'Get AI score' }))

  expect(screen.getByRole('button', { name: 'Scoring...' })).toHaveAttribute('aria-disabled', 'true')
  expect(screen.getByLabelText('Provider')).toBeDisabled()

  fireEvent.click(screen.getByRole('button', { name: 'Scoring...' }))
  expect(mockedScore).toHaveBeenCalledTimes(1)
})

it('says so when the providers cannot be loaded and keeps the button off', async () => {
  mockedProviders.mockRejectedValueOnce(new Error('down')).mockResolvedValue(providers)
  renderWidget()

  expect(await screen.findByRole('alert')).toHaveTextContent('Scoring providers could not be loaded. down')
  expect(screen.getByRole('button', { name: 'Get AI score' })).toHaveAttribute('aria-disabled', 'true')

  fireEvent.click(screen.getByRole('button', { name: 'Try again' }))

  expect(await screen.findByRole('option', { name: 'Claude (claude-haiku-4-5)' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Get AI score' })).toHaveAttribute('aria-disabled', 'false')
})
