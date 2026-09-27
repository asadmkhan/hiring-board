import { useEffect, useState } from 'react'
import { listApplications } from './api'
import { formatDate } from './format'
import type { ApplicationPage } from './types'

type State =
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; page: ApplicationPage }

export default function ApplicationList() {
  const [state, setState] = useState<State>({ kind: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    // A response for an older request must not overwrite a newer one.
    let stale = false
    listApplications()
      .then((page) => {
        if (!stale) setState({ kind: 'ready', page })
      })
      .catch((error: Error) => {
        if (!stale) setState({ kind: 'error', message: error.message })
      })
    return () => {
      stale = true
    }
  }, [attempt])

  const retry = () => {
    setState({ kind: 'loading' })
    setAttempt((n) => n + 1)
  }

  if (state.kind === 'loading') {
    return <p>Loading applications...</p>
  }
  if (state.kind === 'error') {
    return (
      <p role="alert">
        {state.message} <button onClick={retry}>Try again</button>
      </p>
    )
  }
  if (state.page.items.length === 0) {
    return <p>No applications found.</p>
  }

  return (
    <>
      <p>{state.page.total} applications</p>
      <table>
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
          {state.page.items.map((item) => (
            <tr key={item.application_id}>
              <td>{item.candidate.full_name}</td>
              <td>{item.job.title}</td>
              <td>{item.job.job_family}</td>
              <td>{item.job.country}</td>
              <td>{item.match_score}</td>
              <td>{item.match_band}</td>
              <td>{item.status}</td>
              <td>{formatDate(item.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}
