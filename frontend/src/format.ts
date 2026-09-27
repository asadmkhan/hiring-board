// "2026-06-30T15:16:00" -> "2026-06-30 15:16"
export function formatDate(value: string): string {
  return value.replace('T', ' ').slice(0, 16)
}
