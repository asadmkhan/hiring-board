import { STATUS_LABELS } from '../labels'
import type { ApplicationStatus } from '../types'

export default function StatusBadge({ status }: { status: ApplicationStatus }) {
  return <span className={`badge badge-${status}`}>{STATUS_LABELS[status]}</span>
}
