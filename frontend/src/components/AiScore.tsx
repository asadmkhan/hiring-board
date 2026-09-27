import { useEffect, useState, type FormEvent } from 'react'
import { getLlmProviders, messageOf, scoreApplication } from '../api'
import { formatDate } from '../format'
import { bandLabel, providerLabel } from '../labels'
import Field from './Field'
import type { ApplicationLlmScore, LlmProvider } from '../types'

interface Props {
  applicationId: string
  matchScore: number
  matchBand: string
  storedScores: ApplicationLlmScore[]
}

export default function AiScore({ applicationId, matchScore, matchBand, storedScores }: Props) {
  const [scores, setScores] = useState(storedScores)
  const [providers, setProviders] = useState<LlmProvider[] | null>(null)
  const [providersError, setProvidersError] = useState<string | null>(null)
  const [providersAttempt, setProvidersAttempt] = useState(0)
  const [provider, setProvider] = useState('')
  const [scoring, setScoring] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let stale = false
    getLlmProviders()
      .then((loaded) => {
        if (stale) return
        setProviders(loaded)
        setProvider((current) => current || loaded[0]?.id || '')
      })
      .catch((failure: unknown) => {
        if (!stale) setProvidersError(messageOf(failure))
      })
    return () => {
      stale = true
    }
  }, [providersAttempt])

  // The backend label wins. The local map only covers scores whose provider is no longer offered.
  const nameOf = (id: string) => providers?.find((p) => p.id === id)?.label ?? providerLabel(id)

  const retryProviders = () => {
    setProvidersError(null)
    setProvidersAttempt((n) => n + 1)
  }

  const score = (event: FormEvent) => {
    event.preventDefault()
    if (!provider || scoring) return
    setScoring(true)
    setError(null)
    setResult(null)
    scoreApplication(applicationId, provider)
      .then((response) => {
        // One line per provider.
        setScores((current) => [...current.filter((s) => s.provider !== response.provider), response])
        setResult(
          response.cached
            ? `Stored ${nameOf(response.provider)} score reused, the model was not called again.`
            : `New ${nameOf(response.provider)} score stored.`,
        )
      })
      .catch((failure: unknown) => setError(messageOf(failure)))
      .finally(() => setScoring(false))
  }

  return (
    <div className="ai-score">
      <Field label="Rule score (0-1)" value={`${matchScore.toFixed(2)} (${bandLabel(matchBand)})`} />
      {scores.length === 0 ? (
        <p>No AI score yet.</p>
      ) : (
        <ul aria-label="AI scores">
          {scores.map((s) => (
            <li key={s.provider}>
              {nameOf(s.provider)}: {s.score} / 100. {s.reason} ({formatDate(s.scored_at)})
            </li>
          ))}
        </ul>
      )}

      {providers?.length === 0 && <p>No scoring providers are set up on this server.</p>}
      {providersError && (
        <p role="alert">
          Scoring providers could not be loaded. {providersError}{' '}
          <button type="button" onClick={retryProviders}>
            Try again
          </button>
        </p>
      )}
      <form onSubmit={score} aria-label="Get AI score">
        <label>
          Provider
          <select
            value={provider}
            disabled={scoring || !providers}
            onChange={(e) => {
              setProvider(e.target.value)
              setResult(null)
              setError(null)
            }}
          >
            {providers?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label} ({p.model})
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="primary" aria-disabled={!provider || scoring}>
          {scoring ? 'Scoring...' : 'Get AI score'}
        </button>
      </form>
      {error && <p role="alert">AI score unavailable: {error}</p>}
      <p role="status" className={result ? 'ok' : undefined}>
        {providers === null && !providersError ? 'Loading providers...' : (result ?? '')}
      </p>
    </div>
  )
}
