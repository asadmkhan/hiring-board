import { useEffect, useRef, useState } from 'react'
import { getFilterOptions, listApplications, messageOf } from '../api'
import { DEFAULT_FILTERS } from '../filters'
import { formatDate } from '../format'
import { bandLabel, countryLabel } from '../labels'
import type { ApplicationFilters, ApplicationPage, FilterOptions } from '../types'
import Filters from './Filters'
import Pager from './Pager'
import StatusBadge from './StatusBadge'

interface ListState {
  page: ApplicationPage | null
  loading: boolean
  error: string | null
}

interface Props {
  selectedId: string | null
  refreshKey: number
  onSelect: (id: string) => void
}

export default function ApplicationList({ selectedId, refreshKey, onSelect }: Props) {
  const [filters, setFilters] = useState<ApplicationFilters>(DEFAULT_FILTERS)
  const [list, setList] = useState<ListState>({ page: null, loading: true, error: null })
  const [attempt, setAttempt] = useState(0)
  const [options, setOptions] = useState<FilterOptions | null>(null)
  const [optionsError, setOptionsError] = useState<string | null>(null)
  const statusRef = useRef<HTMLParagraphElement>(null)
  const lastSelected = useRef<string | null>(null)

  // A refresh from outside (a save in the panel) must show as loading like any other fetch.
  const [seenRefreshKey, setSeenRefreshKey] = useState(refreshKey)
  if (refreshKey !== seenRefreshKey) {
    setSeenRefreshKey(refreshKey)
    setList((current) => ({ ...current, loading: true }))
  }

  useEffect(() => {
    // When the panel closes, put focus back on the row that opened it.
    if (selectedId === null && lastSelected.current) {
      document.querySelector<HTMLButtonElement>(`button[data-id="${lastSelected.current}"]`)?.focus()
    }
    lastSelected.current = selectedId
  }, [selectedId])

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
  }, [filters, attempt, refreshKey])

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
      <Filters
        filters={filters}
        options={options}
        onChange={changeFilters}
        onReset={() => changeFilters(DEFAULT_FILTERS)}
      />
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
          <PageBody
            page={list.page}
            loading={list.loading}
            selectedId={selectedId}
            onPage={changePage}
            onSelect={onSelect}
          />
        </div>
      )}
    </>
  )
}

interface PageBodyProps {
  page: ApplicationPage
  loading: boolean
  selectedId: string | null
  onPage: (page: number) => void
  onSelect: (id: string) => void
}

function PageBody({ page, loading, selectedId, onPage, onSelect }: PageBodyProps) {
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
              <th className="num">Score</th>
              <th>Band</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {page.items.map((item) => (
              <tr key={item.application_id} className={item.application_id === selectedId ? 'selected' : undefined}>
                <td>
                  <button
                    type="button"
                    className="link"
                    data-id={item.application_id}
                    aria-current={item.application_id === selectedId ? 'true' : undefined}
                    onClick={() => onSelect(item.application_id)}
                  >
                    {item.candidate.full_name}
                  </button>
                </td>
                <td>{item.job.title}</td>
                <td>{item.job.job_family}</td>
                <td>{countryLabel(item.job.country)}</td>
                <td className="num">{item.match_score.toFixed(2)}</td>
                <td>{bandLabel(item.match_band)}</td>
                <td>
                  <StatusBadge status={item.status} />
                </td>
                <td className="nowrap">{formatDate(item.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <Pager page={page.page} pageSize={page.page_size} total={page.total} disabled={loading} onPage={onPage} />
    </>
  )
}
