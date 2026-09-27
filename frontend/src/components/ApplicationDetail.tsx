import { useEffect, useRef, useState, type FormEvent } from 'react'
import { getApplication, messageOf, updateApplication } from '../api'
import { STATUSES } from '../filters'
import { formatDate } from '../format'
import { bandLabel, countryLabel, providerLabel, seniorityLabel, sourceLabel, STATUS_LABELS } from '../labels'
import type { ApplicationDetail as Detail, ApplicationStatus, ApplicationUpdate } from '../types'

interface Props {
  id: string
  onChanged: () => void
  onClose: () => void
}

interface Form {
  status: ApplicationStatus
  note: string
}

function formFor(detail: Detail): Form {
  return { status: detail.status, note: detail.note ?? '' }
}

// Only what differs from the saved record is sent. An empty note box clears the note.
function changesBetween(detail: Detail, form: Form): ApplicationUpdate {
  const changes: ApplicationUpdate = {}
  if (form.status !== detail.status) changes.status = form.status
  const note = form.note.trim() || null
  const savedNote = detail.note?.trim() || null
  if (note !== savedNote) changes.note = note
  return changes
}

function years(count: number): string {
  return count === 1 ? '1 year' : `${count} years`
}

export default function ApplicationDetail({ id, onChanged, onClose }: Props) {
  const [detail, setDetail] = useState<Detail | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)
  const [form, setForm] = useState<Form | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const headingRef = useRef<HTMLHeadingElement>(null)
  const saveStatusRef = useRef<HTMLParagraphElement>(null)

  useEffect(() => {
    let stale = false
    getApplication(id)
      .then((loaded) => {
        if (stale) return
        setDetail(loaded)
        setForm(formFor(loaded))
      })
      .catch((error: unknown) => {
        if (!stale) setLoadError(messageOf(error))
      })
    return () => {
      stale = true
    }
  }, [id, attempt])

  // Keyboard users land in the panel when it opens.
  useEffect(() => {
    if (detail) headingRef.current?.focus()
  }, [detail])

  const retry = () => {
    setLoadError(null)
    setAttempt((n) => n + 1)
  }

  const edit = (change: Partial<Form>) => {
    setForm((current) => (current ? { ...current, ...change } : current))
    setSaved(false)
    setSaveError(null)
  }

  const dirty = detail !== null && form !== null && Object.keys(changesBetween(detail, form)).length > 0

  const save = (event: FormEvent) => {
    event.preventDefault()
    if (!detail || !form || !dirty || saving) return
    setSaving(true)
    setSaveError(null)
    updateApplication(id, changesBetween(detail, form))
      .then((updated) => {
        setDetail(updated)
        setForm(formFor(updated))
        setSaved(true)
        onChanged()
        saveStatusRef.current?.focus()
      })
      .catch((error: unknown) => setSaveError(messageOf(error)))
      .finally(() => setSaving(false))
  }

  if (loadError) {
    return (
      <aside className="detail" aria-label="Application details">
        <p role="alert">
          {loadError} <button onClick={retry}>Try again</button> <button onClick={onClose}>Close</button>
        </p>
      </aside>
    )
  }
  if (!detail || !form) {
    return (
      <aside className="detail" aria-label="Application details">
        <p role="status">Loading application...</p>
      </aside>
    )
  }

  const { candidate, job } = detail

  return (
    <aside className="detail" aria-label="Application details">
      <header>
        <h2 tabIndex={-1} ref={headingRef}>
          {candidate.full_name}
        </h2>
        <button onClick={onClose} disabled={saving}>
          Close
        </button>
      </header>

      <h3>Application</h3>
      <Field label="Id" value={detail.application_id} />
      <Field label="Created" value={formatDate(detail.created_at)} />
      <Field label="Source" value={sourceLabel(detail.source)} />
      <Field label="Match score" value={`${detail.match_score} (${bandLabel(detail.match_band)})`} />
      <Field label="Status" value={STATUS_LABELS[detail.status]} />
      <Field label="Status changed" value={detail.status_updated_at ? formatDate(detail.status_updated_at) : 'never'} />

      <h3>Candidate</h3>
      <Field label="Email" value={candidate.email} />
      <Field label="Location" value={`${candidate.city} (${countryLabel(candidate.country)})`} />
      <Field label="Experience" value={years(candidate.years_experience)} />
      <Field label="Prefers" value={candidate.preferred_job_family} />

      <h3>Job</h3>
      <Field label="Title" value={job.title} />
      <Field label="Family" value={`${job.job_family}, ${seniorityLabel(job.seniority)}`} />
      <Field label="Location" value={`${job.city} (${countryLabel(job.country)})`} />
      <Field label="Posted" value={formatDate(job.created_at)} />

      <h3>AI scores</h3>
      {detail.llm_scores.length === 0 ? (
        <p>No AI score yet.</p>
      ) : (
        <ul>
          {detail.llm_scores.map((score) => (
            <li key={score.provider}>
              {providerLabel(score.provider)}: {score.score} / 100. {score.reason} ({formatDate(score.scored_at)})
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={save} aria-label="Change status">
        <label>
          Status
          <select
            value={form.status}
            disabled={saving}
            onChange={(e) => edit({ status: e.target.value as ApplicationStatus })}
          >
            {STATUSES.map((status) => (
              <option key={status} value={status}>
                {STATUS_LABELS[status]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Note
          <textarea
            value={form.note}
            rows={3}
            maxLength={500}
            disabled={saving}
            onChange={(e) => edit({ note: e.target.value })}
          />
        </label>
        <div>
          <button type="submit" aria-disabled={!dirty || saving}>
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
        {saveError && <p role="alert">{saveError}</p>}
        <p role="status" tabIndex={-1} ref={saveStatusRef}>
          {saved ? 'Saved.' : ''}
        </p>
      </form>
    </aside>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="field">
      <span>{label}</span>
      {value}
    </div>
  )
}
