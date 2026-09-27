import { useState, type FormEvent } from 'react'
import { SORT_OPTIONS, STATUSES } from '../filters'
import { countryLabel, STATUS_LABELS } from '../labels'
import type { ApplicationFilters, ApplicationStatus, FilterOptions, SortKey } from '../types'

interface Props {
  filters: ApplicationFilters
  options: FilterOptions | null
  onChange: (change: Partial<ApplicationFilters>) => void
  onReset: () => void
}

export default function Filters({ filters, options, onChange, onReset }: Props) {
  const [text, setText] = useState(filters.q)

  // Reset and other outside changes to the search must show in the box.
  const [seenQ, setSeenQ] = useState(filters.q)
  if (filters.q !== seenQ) {
    setSeenQ(filters.q)
    setText(filters.q)
  }

  // Whatever is in the box counts, also when another filter changes.
  const apply = (change: Partial<ApplicationFilters>) => onChange({ ...change, q: text.trim() })

  const search = (event: FormEvent) => {
    event.preventDefault()
    setText(text.trim())
    apply({})
  }

  const typeSearch = (value: string) => {
    setText(value)
    if (value === '' && filters.q) onChange({ q: '' })
  }

  const reset = () => {
    setText('')
    onReset()
  }

  return (
    <div className="filters">
      <form onSubmit={search} className="search" role="search" aria-label="Search applications">
        <label>
          Search
          <input
            type="search"
            value={text}
            maxLength={100}
            placeholder="Candidate or job title"
            onChange={(e) => typeSearch(e.target.value)}
          />
        </label>
        <button type="submit">Search</button>
      </form>
      <label>
        Status
        <select
          value={filters.status}
          onChange={(e) => apply({ status: e.target.value as ApplicationStatus | '' })}
        >
          <option value="">All</option>
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {STATUS_LABELS[status]}
            </option>
          ))}
        </select>
      </label>
      <label>
        Country
        <select value={filters.country} onChange={(e) => apply({ country: e.target.value })}>
          <option value="">All</option>
          {options?.countries.map((country) => (
            <option key={country} value={country}>
              {countryLabel(country)}
            </option>
          ))}
        </select>
      </label>
      <label>
        Job family
        <select value={filters.job_family} onChange={(e) => apply({ job_family: e.target.value })}>
          <option value="">All</option>
          {options?.job_families.map((family) => (
            <option key={family} value={family}>
              {family}
            </option>
          ))}
        </select>
      </label>
      <label>
        Sort
        <select value={filters.sort} onChange={(e) => apply({ sort: e.target.value as SortKey })}>
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <button type="button" onClick={reset}>
        Reset
      </button>
    </div>
  )
}
