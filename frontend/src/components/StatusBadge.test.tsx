import { render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'
import StatusBadge from './StatusBadge'

it('shows the readable word with a class per status', () => {
  render(<StatusBadge status="in_review" />)

  const badge = screen.getByText('In review')
  expect(badge).toHaveClass('badge', 'badge-in_review')
})
