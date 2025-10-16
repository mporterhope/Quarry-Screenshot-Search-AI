import { render, screen } from '@testing-library/react'
import SmartActions from './SmartActions'

describe('SmartActions', () => {
  it('renders calendar link when date present', () => {
    render(<SmartActions entities={{ date: ['22 Nov 2025 3:30 PM'] }} />)
    expect(screen.getByText(/Add to Calendar/i)).toBeInTheDocument()
  })

  it('renders link/mail/phone when entities present', () => {
    render(<SmartActions entities={{ url: ['https://example.com'], email: ['a@b.com'], phone: ['(555) 555-1212'] }} />)
    expect(screen.getByText(/Open Link/i)).toBeInTheDocument()
    expect(screen.getByText(/Email/i)).toBeInTheDocument()
    expect(screen.getByText(/Call/i)).toBeInTheDocument()
  })
})


