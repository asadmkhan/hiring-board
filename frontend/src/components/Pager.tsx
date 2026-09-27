interface Props {
  page: number
  pageSize: number
  total: number
  disabled: boolean
  onPage: (page: number) => void
}

export default function Pager({ page, pageSize, total, disabled, onPage }: Props) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  return (
    <div className="pager">
      <button disabled={disabled || page <= 1} onClick={() => onPage(page - 1)}>
        Previous
      </button>
      <span>
        Page {page} of {pages}, {total} {total === 1 ? 'application' : 'applications'}
      </span>
      <button disabled={disabled || page >= pages} onClick={() => onPage(page + 1)}>
        Next
      </button>
    </div>
  )
}
