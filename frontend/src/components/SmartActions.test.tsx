import { render, screen } from '@testing-library/react'
import SmartActions from './SmartActions'

describe('SmartActions', () => {
  it('renders calendar link when date present', () => {
    render(<SmartActions entities={{ date: ['22 Nov 2025 3:30 PM'] }} />)
    const calendarLink = screen.getByText(/Add to Calendar/i)
    expect(calendarLink).toBeInTheDocument()
    expect(calendarLink.closest('a')).toHaveAttribute('href', expect.stringContaining('calendar.google.com'))
  })

  it('renders link/mail/phone when entities present', () => {
    render(<SmartActions entities={{ url: ['https://example.com'], email: ['a@b.com'], phone: ['(555) 555-1212'] }} />)
    expect(screen.getByText(/Open Link/i)).toBeInTheDocument()
    expect(screen.getByText(/Email/i)).toBeInTheDocument()
    expect(screen.getByText(/Call/i)).toBeInTheDocument()
  })

  it('generates timezone-aware calendar URLs', () => {
    // Force timezone offset so generated URL uses local offset instead of Z
    const offsetSpy = vi.spyOn(Date.prototype, 'getTimezoneOffset').mockReturnValue(-300)

    render(<SmartActions entities={{ date: ['22 Nov 2025 3:30 PM'] }} />)
    const calendarLink = screen.getByText(/Add to Calendar/i).closest('a')

    // Should contain timezone offset, not Z (UTC)
    expect(calendarLink).toHaveAttribute('href', expect.stringContaining('+05:00'))
    expect(calendarLink).not.toHaveAttribute('href', expect.stringContaining('Z'))

    offsetSpy.mockRestore()
  })
})


