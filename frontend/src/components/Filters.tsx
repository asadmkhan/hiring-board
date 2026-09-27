import { SORT_OPTIONS, STATUSES } from '../filters'
import { countryLabel, STATUS_LABELS } from '../labels'
import type { ApplicationFilters, ApplicationStatus, FilterOptions, SortKey } from '../types'

interface Props {
  filters: ApplicationFilters
  options: FilterOptions | null
  onChange: (change: Partial<ApplicationFilters>) => void
}

export default function Filters({ filters, options, onChange }: Props) {
  return (
    <div className="filters">
      <label>
        Status
        <select
          value={filters.status}
          onChange={(e) => onChange({ status: e.target.value as ApplicationStatus | '' })}
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
        <select value={filters.country} onChange={(e) => onChange({ country: e.target.value })}>
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
        <select value={filters.job_family} onChange={(e) => onChange({ job_family: e.target.value })}>
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
        <select value={filters.sort} onChange={(e) => onChange({ sort: e.target.value as SortKey })}>
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
