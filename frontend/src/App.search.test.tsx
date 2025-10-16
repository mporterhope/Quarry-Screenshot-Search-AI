import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from './App'

const mockFetch = vi.fn()
vi.spyOn(global, 'fetch' as any).mockImplementation(mockFetch)

describe('App search', () => {
  beforeEach(() => {
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/albums')) {
        return Promise.resolve(new Response(JSON.stringify({ albums: [{ id: 'alb_123', name: 'Test Album' }] })))
      }
      if (url.includes('/search')) {
        return Promise.resolve(new Response(JSON.stringify({ query: 'test', results: [] })))
      }
      return Promise.resolve(new Response('{}'))
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows search UI', () => {
    render(<App />)
    expect(screen.getByPlaceholderText(/Search…/i)).toBeInTheDocument()
  })

  it('allows album-only search without manual query', async () => {
    render(<App />)
    
    // Wait for albums to load
    await waitFor(() => {
      expect(screen.getByText('Test Album')).toBeInTheDocument()
    })
    
    // Select album
    const albumSelect = screen.getByDisplayValue('Select album…')
    fireEvent.change(albumSelect, { target: { value: 'alb_123' } })
    
    // Search button should be enabled (no manual query needed)
    const searchButton = screen.getByText('Search')
    expect(searchButton).not.toBeDisabled()
    
    // Click search
    fireEvent.click(searchButton)
    
    // Should call search with album_id
    await waitFor(() => {
      const searchCall = mockFetch.mock.calls.find(([url]) => typeof url === 'string' && url.includes('/search'))
      expect(searchCall).toBeTruthy()
      const url = String(searchCall?.[0])
      expect(url).toContain('album_id=alb_123')
      expect(url).not.toContain('q=')
    })
  })

  it('enables search with text query only', () => {
    render(<App />)
    
    const searchInput = screen.getByPlaceholderText(/Search…/i)
    const searchButton = screen.getByText('Search')
    
    // Initially disabled
    expect(searchButton).toBeDisabled()
    
    // Type query
    fireEvent.change(searchInput, { target: { value: 'test query' } })
    
    // Should be enabled
    expect(searchButton).not.toBeDisabled()
  })
})


