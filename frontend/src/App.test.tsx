import { render, screen } from '@testing-library/react'
import App from './App'

// Mock fetch to avoid backend dependency in tests
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ albums: [] }),
  })
) as any

describe('App smoke', () => {
  it('renders title', () => {
    render(<App />)
    expect(screen.getByText(/Quarry.io/i)).toBeInTheDocument()
  })
})


