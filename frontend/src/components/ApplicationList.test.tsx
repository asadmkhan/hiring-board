import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { getFilterOptions, listApplications } from '../api'
import type { ApplicationFilters, ApplicationPage } from '../types'
import ApplicationList from './ApplicationList'

vi.mock('../api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api')>()),
  listApplications: vi.fn(),
  getFilterOptions: vi.fn(),
}))
const mockedList = vi.mocked(listApplications)
const mockedOptions = vi.mocked(getFilterOptions)

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

// Answers like the backend: echoes the requested page number.
function answerWith(total: number, items = page.items) {
  mockedList.mockImplementation((filters: ApplicationFilters) =>
    Promise.resolve({ ...page, items, total, page: filters.page }),
  )
}

const onSelect = vi.fn()

function renderList(selectedId: string | null = null, refreshKey = 0) {
  return render(<ApplicationList selectedId={selectedId} refreshKey={refreshKey} onSelect={onSelect} />)
}

beforeEach(() => {
  onSelect.mockReset()
  mockedList.mockReset()
  mockedOptions.mockReset()
  mockedOptions.mockResolvedValue({ countries: ['AT', 'DE'], job_families: ['IT', 'Logistics'] })
})

it('shows the loading text first', () => {
  mockedList.mockReturnValue(new Promise(() => {}))

  renderList()

  expect(screen.getByText('Loading applications...')).toBeInTheDocument()
})

it('shows one row per application', async () => {
  answerWith(1)

  renderList()

  expect(await screen.findByText('Anna Adler')).toBeInTheDocument()
  expect(screen.getByText('Warehouse Associate')).toBeInTheDocument()
  expect(screen.getByText('2026-03-01 09:00')).toBeInTheDocument()
  expect(screen.getByRole('cell', { name: 'Germany' })).toBeInTheDocument()
  expect(screen.getByRole('cell', { name: '0.50' })).toBeInTheDocument()
  expect(screen.getByRole('cell', { name: 'New' })).toBeInTheDocument()
  expect(screen.getByText('Page 1 of 1, 1 application')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()
})

it('shows the empty message', async () => {
  answerWith(0, [])

  renderList()

  expect(await screen.findByText('No applications found.')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Previous' })).not.toBeInTheDocument()
})

it('keeps the pager on an empty page past the end', async () => {
  answerWith(50)
  renderList()
  await screen.findByText('Anna Adler')
  answerWith(21, [])

  fireEvent.click(screen.getByRole('button', { name: 'Next' }))

  expect(await screen.findByText('No applications on this page.')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Previous' })).toBeEnabled()
})

it('shows the error message with a retry button', async () => {
  mockedList.mockRejectedValue(new Error('Could not reach the server.'))

  renderList()

  expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach the server.')
  expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
})

it('fills the dropdowns from the filter options', async () => {
  answerWith(1)

  renderList()

  expect(await screen.findByRole('option', { name: 'Logistics' })).toBeInTheDocument()
  expect(screen.getByRole('option', { name: 'Austria' })).toBeInTheDocument()
  expect(screen.getByRole('option', { name: 'In review' })).toBeInTheDocument()
})

it('says so when the filter options cannot be loaded', async () => {
  answerWith(1)
  mockedOptions.mockRejectedValue(new Error('down'))

  renderList()

  expect(await screen.findByRole('alert')).toHaveTextContent('Filter values could not be loaded.')
  expect(await screen.findByText('Anna Adler')).toBeInTheDocument()
})

it('reloads from page 1 when a filter changes and keeps the table on screen', async () => {
  answerWith(50)
  renderList()
  await screen.findByText('Anna Adler')
  fireEvent.click(screen.getByRole('button', { name: 'Next' }))
  await screen.findByText('Page 2 of 3, 50 applications')

  fireEvent.change(screen.getByLabelText('Country'), { target: { value: 'AT' } })

  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ country: 'AT', page: 1 }))
  expect(screen.getByRole('status')).toHaveTextContent('Loading applications...')
  expect(screen.getByText('Anna Adler')).toBeInTheDocument()
  expect(await screen.findByText('Page 1 of 3, 50 applications')).toBeInTheDocument()
})

it('pages forward and back and keeps the filters', async () => {
  answerWith(50)
  renderList()
  await screen.findByText('Anna Adler')
  fireEvent.change(screen.getByLabelText('Sort'), { target: { value: 'highest_score' } })
  await screen.findByText('Page 1 of 3, 50 applications')
  expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled()

  fireEvent.click(screen.getByRole('button', { name: 'Next' }))
  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ sort: 'highest_score', page: 2 }))
  await screen.findByText('Page 2 of 3, 50 applications')

  fireEvent.click(screen.getByRole('button', { name: 'Previous' }))
  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ sort: 'highest_score', page: 1 }))
  expect(await screen.findByText('Page 1 of 3, 50 applications')).toBeInTheDocument()
})

it('recovers after a retry', async () => {
  mockedList.mockRejectedValueOnce(new Error('Could not reach the server.'))
  renderList()
  await screen.findByRole('alert')
  answerWith(1)

  fireEvent.click(screen.getByRole('button', { name: 'Try again' }))

  expect(await screen.findByText('Anna Adler')).toBeInTheDocument()
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
})

it('ignores a slow answer to an older request', async () => {
  let answerFirst: (page: ApplicationPage) => void = () => {}
  mockedList
    .mockImplementationOnce(() => new Promise((resolve) => (answerFirst = resolve)))
    .mockImplementation((filters: ApplicationFilters) =>
      Promise.resolve({ ...page, total: 5, page: filters.page, items: [] }),
    )
  renderList()
  fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'hired' } })
  await screen.findByText('No applications on this page.')

  answerFirst({ ...page, total: 1 })

  await new Promise((resolve) => setTimeout(resolve, 0))
  expect(screen.queryByText('Anna Adler')).not.toBeInTheDocument()
})

it('retries the filter options together with the list', async () => {
  answerWith(1)
  mockedOptions.mockRejectedValueOnce(new Error('down'))
  renderList()
  await screen.findByRole('alert')

  fireEvent.click(screen.getByRole('button', { name: 'Try again' }))

  expect(await screen.findByRole('option', { name: 'Logistics' })).toBeInTheDocument()
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
})

it('blocks the pager while a new page loads', async () => {
  answerWith(50)
  renderList()
  await screen.findByText('Anna Adler')
  mockedList.mockReturnValue(new Promise(() => {}))

  fireEvent.change(screen.getByLabelText('Job family'), { target: { value: 'Logistics' } })

  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ job_family: 'Logistics', page: 1 }))
  expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled()
})

it('reports the clicked application and highlights the selected row', async () => {
  answerWith(1)
  renderList('A1')

  fireEvent.click(await screen.findByRole('button', { name: 'Anna Adler' }))

  expect(onSelect).toHaveBeenCalledWith('A1')
  expect(screen.getByRole('button', { name: 'Anna Adler' }).closest('tr')).toHaveClass('selected')
})

it('reloads with the same filters and page when asked from outside', async () => {
  answerWith(50)
  const view = renderList()
  await screen.findByText('Anna Adler')
  fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'hired' } })
  await screen.findByText('Page 1 of 3, 50 applications')
  fireEvent.click(screen.getByRole('button', { name: 'Next' }))
  await screen.findByText('Page 2 of 3, 50 applications')
  const calls = mockedList.mock.calls.length

  view.rerender(<ApplicationList selectedId={null} refreshKey={1} onSelect={onSelect} />)

  expect(mockedList.mock.calls.length).toBe(calls + 1)
  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ status: 'hired', page: 2 }))
  expect(screen.getByRole('status')).toHaveTextContent('Loading applications...')
  expect(await screen.findByText('Page 2 of 3, 50 applications')).toBeInTheDocument()
})

it('resets the filters to the defaults', async () => {
  answerWith(50)
  renderList()
  await screen.findByText('Anna Adler')
  fireEvent.change(screen.getByLabelText('Country'), { target: { value: 'AT' } })
  fireEvent.change(screen.getByLabelText('Job family'), { target: { value: 'Logistics' } })
  await screen.findByText('Page 1 of 3, 50 applications')
  fireEvent.click(screen.getByRole('button', { name: 'Next' }))
  await screen.findByText('Page 2 of 3, 50 applications')

  fireEvent.click(screen.getByRole('button', { name: 'Reset' }))

  expect(mockedList).toHaveBeenLastCalledWith(
    expect.objectContaining({ country: '', job_family: '', q: '', status: '', sort: 'newest', page: 1 }),
  )
  expect(await screen.findByLabelText('Country')).toHaveValue('')
})

it('applies the search on submit and resets to page 1', async () => {
  answerWith(50)
  renderList()
  await screen.findByText('Anna Adler')
  fireEvent.click(screen.getByRole('button', { name: 'Next' }))
  await screen.findByText('Page 2 of 3, 50 applications')

  fireEvent.change(screen.getByLabelText('Search'), { target: { value: '  nurse ' } })
  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 }))
  fireEvent.submit(screen.getByRole('search'))

  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'nurse', page: 1 }))

  fireEvent.click(screen.getByRole('button', { name: 'Reset' }))
  expect(await screen.findByLabelText('Search')).toHaveValue('')
})

it('search button submits and blank text means no search', async () => {
  answerWith(50)
  renderList()
  await screen.findByText('Anna Adler')

  fireEvent.change(screen.getByLabelText('Search'), { target: { value: 'care' } })
  fireEvent.click(screen.getByRole('button', { name: 'Search' }))
  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'care' }))

  fireEvent.change(screen.getByLabelText('Search'), { target: { value: '   ' } })
  fireEvent.click(screen.getByRole('button', { name: 'Search' }))
  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ q: '' }))
  expect(screen.getByLabelText('Search')).toHaveValue('')
})

it('clears the search when the box is emptied and on reset with unsent text', async () => {
  answerWith(50)
  renderList()
  await screen.findByText('Anna Adler')
  fireEvent.change(screen.getByLabelText('Search'), { target: { value: 'care' } })
  fireEvent.submit(screen.getByRole('search'))
  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'care' }))

  fireEvent.change(screen.getByLabelText('Search'), { target: { value: '' } })
  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ q: '' }))

  fireEvent.change(screen.getByLabelText('Search'), { target: { value: 'typed' } })
  fireEvent.click(screen.getByRole('button', { name: 'Reset' }))
  expect(screen.getByLabelText('Search')).toHaveValue('')
  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ q: '' }))
})

it('applies the typed search when another filter changes', async () => {
  answerWith(50)
  renderList()
  await screen.findByText('Anna Adler')

  fireEvent.change(screen.getByLabelText('Search'), { target: { value: 'care' } })
  fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'hired' } })

  expect(mockedList).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'care', status: 'hired', page: 1 }))
})
