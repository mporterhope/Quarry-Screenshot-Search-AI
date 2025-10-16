import { render, screen } from '@testing-library/react'
import App from './App'

vi.spyOn(global, 'fetch' as any).mockImplementation((url: string) => {
  if (url.includes('/albums')) {
    return Promise.resolve(new Response(JSON.stringify({ albums: [] })))
  }
  if (url.includes('/search')) {
    return Promise.resolve(new Response(JSON.stringify({ query: 'test', results: [] })))
  }
  return Promise.resolve(new Response('{}'))
})

describe('App search', () => {
  it('shows search UI', () => {
    render(<App />)
    expect(screen.getByPlaceholderText(/Search…/i)).toBeInTheDocument()
  })
})


