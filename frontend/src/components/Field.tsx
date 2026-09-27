import type { ReactNode } from 'react'

export default function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="field">
      <span>{label}</span>
      <span className="value">{value}</span>
    </div>
  )
}
