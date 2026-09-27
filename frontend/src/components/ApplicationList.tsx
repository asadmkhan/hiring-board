import { useEffect, useRef, useState } from 'react'
import { getFilterOptions, listApplications } from '../api'
import { DEFAULT_FILTERS } from '../filters'
import { formatDate } from '../format'
import { bandLabel, countryLabel, STATUS_LABELS } from '../labels'
import type { ApplicationFilters, ApplicationPage, FilterOptions } from '../types'
import Filters from './Filters'
import Pager from './Pager'

interface ListState {
  page: ApplicationPage | null
  loading: boolean
  error: string | null
}

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong.'
}

export default function ApplicationList() {
  const [filters, setFilters] = useState<ApplicationFilters>(DEFAULT_FILTERS)
  const [list, setList] = useState<ListState>({ page: null, loading: true, error: null })
  const [attempt, setAttempt] = useState(0)
  const [options, setOptions] = useState<FilterOptions | null>(null)
  const [optionsError, setOptionsError] = useState<string | null>(null)
  const statusRef = useRef<HTMLParagraphElement>(null)

  useEffect(() => {
    if (options) return
    let stale = false
    getFilterOptions()
      .then((loaded) => {
        if (!stale) setOptions(loaded)
      })
      .catch((error: unknown) => {
        if (!stale) setOptionsError(messageOf(error))
      })
    return () => {
      stale = true
    }
  }, [options, attempt])

  useEffect(() => {
    // A response for an older request must not overwrite a newer one.
    let stale = false
    listApplications(filters)
      .then((page) => {
        if (!stale) setList({ page, loading: false, error: null })
      })
      .catch((error: unknown) => {
        if (!stale) setList({ page: null, loading: false, error: messageOf(error) })
      })
    return () => {
      stale = true
    }
  }, [filters, attempt])

  const startLoading = () => setList((current) => ({ ...current, loading: true, error: null }))

  const changeFilters = (change: Partial<ApplicationFilters>) => {
    startLoading()
    setFilters((current) => ({ ...current, ...change, page: 1 }))
  }

  const changePage = (page: number) => {
    startLoading()
    setFilters((current) => ({ ...current, page }))
  }

  const retry = () => {
    startLoading()
    setOptionsError(null)
    setAttempt((n) => n + 1)
    // The button that had focus is about to go away. Park focus on the status line.
    statusRef.current?.focus()
  }

  return (
    <>
      <Filters filters={filters} options={options} onChange={changeFilters} />
      {optionsError && (
        <p role="alert">
          Filter values could not be loaded. {optionsError} <button onClick={retry}>Try again</button>
        </p>
      )}
      {list.error && (
        <p role="alert">
          {list.error} <button onClick={retry}>Try again</button>
        </p>
      )}
      <p role="status" tabIndex={-1} ref={statusRef}>
        {list.loading ? 'Loading applications...' : ''}
      </p>
      {list.page && (
        <div aria-busy={list.loading}>
          <PageBody page={list.page} loading={list.loading} onPage={changePage} />
        </div>
      )}
    </>
  )
}

interface PageBodyProps {
  page: ApplicationPage
  loading: boolean
  onPage: (page: number) => void
}

function PageBody({ page, loading, onPage }: PageBodyProps) {
  if (page.total === 0) {
    return <p>No applications found.</p>
  }
  return (
    <>
      {page.items.length === 0 ? (
        <p>No applications on this page.</p>
      ) : (
        <table aria-label="Applications">
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Job</th>
              <th>Family</th>
              <th>Country</th>
              <th>Score</th>
              <th>Band</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {page.items.map((item) => (
              <tr key={item.application_id}>
                <td>{item.candidate.full_name}</td>
                <td>{item.job.title}</td>
                <td>{item.job.job_family}</td>
                <td>{countryLabel(item.job.country)}</td>
                <td>{item.match_score}</td>
                <td>{bandLabel(item.match_band)}</td>
                <td>{STATUS_LABELS[item.status]}</td>
                <td>{formatDate(item.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <Pager page={page.page} pageSize={page.page_size} total={page.total} disabled={loading} onPage={onPage} />
    </>
  )
}
