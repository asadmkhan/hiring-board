import { afterEach, expect, it, vi } from 'vitest'
import { listApplications } from './api'
import { DEFAULT_FILTERS } from './filters'

function stubFetch() {
  const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
})

it('sends only the sort and paging params when no filter is set', async () => {
  const fetchMock = stubFetch()

  await listApplications(DEFAULT_FILTERS)

  const url = new URL(fetchMock.mock.calls[0][0])
  expect(url.pathname).toBe('/applications')
  expect(Object.fromEntries(url.searchParams)).toEqual({
    sort: 'created_at',
    order: 'desc',
    page: '1',
    page_size: '20',
  })
})

it('encodes the filters and maps the sort key', async () => {
  const fetchMock = stubFetch()

  await listApplications({
    status: 'new',
    country: 'AT',
    job_family: 'Office & Admin',
    q: 'Mia B',
    sort: 'highest_score',
    page: 3,
  })

  const url = new URL(fetchMock.mock.calls[0][0])
  expect(url.search).toContain('job_family=Office+%26+Admin')
  expect(Object.fromEntries(url.searchParams)).toMatchObject({
    status: 'new',
    country: 'AT',
    job_family: 'Office & Admin',
    q: 'Mia B',
    sort: 'match_score',
    order: 'desc',
    page: '3',
  })
})

it('turns a network failure into a readable error', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

  await expect(listApplications(DEFAULT_FILTERS)).rejects.toThrow('Could not reach the server.')
})

it('uses the detail text of a backend error', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"detail":"Application not found"}', { status: 404 })))

  await expect(listApplications(DEFAULT_FILTERS)).rejects.toThrow('Application not found')
})

it('joins the messages of a validation error', async () => {
  const body = '{"detail":[{"msg":"Input should be 1 or more"},{"msg":"Input should be less than 101"}]}'
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(body, { status: 422 })))

  await expect(listApplications(DEFAULT_FILTERS)).rejects.toThrow(
    'Input should be 1 or more, Input should be less than 101',
  )
})

it('falls back to the status code when the error body is not JSON', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>oops</html>', { status: 502 })))

  await expect(listApplications(DEFAULT_FILTERS)).rejects.toThrow('Request failed (502)')
})

it('reports an unreadable success body', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>', { status: 200 })))

  await expect(listApplications(DEFAULT_FILTERS)).rejects.toThrow('The server sent an unreadable response.')
})
