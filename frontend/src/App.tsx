import ImageDetail from './components/ImageDetail'
import React, { useMemo, useState } from 'react'

type SearchResult = {
  id: string
  filename: string
  text: string
  width: number
  height: number
  collection?: string | null
  score: number
  image_path: string
  entities?: Record<string, string[]>
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App() {
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [error, setError] = useState<string | null>(null)
  const [entityType, setEntityType] = useState<string>('')
  const [typeLabel, setTypeLabel] = useState<string>('')
  const [albums, setAlbums] = useState<Array<{id: string; name: string}>>([])
  const [detailId, setDetailId] = useState<string | null>(null)
  const [newAlbumName, setNewAlbumName] = useState('')
  const [albumId, setAlbumId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [askQuestion, setAskQuestion] = useState('')
  const [askAnswer, setAskAnswer] = useState<{answer: string; citations: Array<{image_id: string; filename: string; text_snippet: string; score: number; image_path: string}>} | null>(null)

  const canSearch = useMemo(() => query.trim().length > 0 || albumId.length > 0, [query, albumId])

  async function handleUpload() {
    if (files.length === 0) return
    setUploading(true)
    setError(null)
    try {
      const form = new FormData()
      files.forEach(f => form.append('files', f))
      const res = await fetch(`${API_BASE}/index`, { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      await res.json()
    } catch (e: any) {
      setError(String(e.message || e))
    } finally {
      setUploading(false)
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!canSearch) return
    setError(null)
    try {
      const params = new URLSearchParams()
      if (query.trim().length > 0) {
        params.set('q', query)
      }
      if (entityType) params.set('entity_type', entityType)
      if (albumId) params.set('album_id', albumId)
      if (startDate) params.set('start_date', startDate)
      if (endDate) params.set('end_date', endDate)
      if (typeLabel) params.set('type_label', typeLabel)
      const res = await fetch(`${API_BASE}/search?${params.toString()}`)
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setResults(data.results)
    } catch (e: any) {
      setError(String(e.message || e))
    }
  }

  async function refreshAlbums() {
    const res = await fetch(`${API_BASE}/albums`)
    if (!res.ok) return
    const data = await res.json()
    setAlbums((data.albums || []).map((a: any) => ({ id: a.id, name: a.name })))
  }

  async function handleCreateAlbum(e: React.FormEvent) {
    e.preventDefault()
    if (!newAlbumName.trim()) return
    const rule = { q: query || undefined, entity_type: entityType || undefined, start_date: startDate || undefined, end_date: endDate || undefined }
    const form = new FormData()
    form.set('name', newAlbumName)
    form.set('rule', JSON.stringify(rule))
    const res = await fetch(`${API_BASE}/albums`, { method: 'POST', body: form })
    if (res.ok) {
      setNewAlbumName('')
      await refreshAlbums()
    }
  }

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault()
    if (!askQuestion.trim()) return
    setError(null)
    try {
      const form = new FormData()
      form.set('question', askQuestion)
      const res = await fetch(`${API_BASE}/ask`, { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setAskAnswer(data)
    } catch (e: any) {
      setError(String(e.message || e))
    }
  }

  React.useEffect(() => { refreshAlbums() }, [])

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', padding: 24, fontFamily: 'ui-sans-serif, system-ui' }}>
      <h1>Quarry.io</h1>
      <p>Index screenshots with OCR and search them semantically.</p>

      <section style={{ marginBottom: 24 }}>
        <input type="file" multiple accept="image/*" onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
        <button onClick={handleUpload} disabled={uploading || files.length === 0} style={{ marginLeft: 12 }}>
          {uploading ? 'Uploading…' : 'Index Selected'}
        </button>
      </section>

      <form onSubmit={handleSearch} style={{ marginBottom: 12, display: 'flex', gap: 12, alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Search…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ flex: 1, padding: 8 }}
        />
        <select value={entityType} onChange={(e) => setEntityType(e.target.value)}>
          <option value="">All entities</option>
          <option value="url">URL</option>
          <option value="email">Email</option>
          <option value="phone">Phone</option>
          <option value="date">Date</option>
          <option value="amount">Amount</option>
          <option value="code">Code</option>
        </select>
        <select value={typeLabel} onChange={(e) => setTypeLabel(e.target.value)}>
          <option value="">All types</option>
          <option value="receipt">Receipt</option>
          <option value="booking">Booking</option>
          <option value="chat">Chat</option>
          <option value="code">Code</option>
          <option value="slide">Slide</option>
          <option value="whiteboard">Whiteboard</option>
          <option value="article">Article</option>
          <option value="map">Map</option>
        </select>
        <label style={{ fontSize: 12 }}>From <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} /></label>
        <label style={{ fontSize: 12 }}>To <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} /></label>
        <button type="submit" disabled={!canSearch} style={{ marginLeft: 12 }}>Search</button>
      </form>

      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 24 }}>
        <select value={albumId} onChange={(e) => setAlbumId(e.target.value)}>
          <option value="">Select album…</option>
          {albums.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
        </select>
        <form onSubmit={handleCreateAlbum} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input type="text" placeholder="New album name" value={newAlbumName} onChange={(e) => setNewAlbumName(e.target.value)} />
          <button type="submit">Save current query as album</button>
        </form>
        {!!albumId && (
          <>
            <button onClick={async () => { const name = prompt('Rename album to?'); if (name) { const f = new FormData(); f.set('name', name); await fetch(`${API_BASE}/albums/${albumId}/rename`, { method: 'POST', body: f }); await refreshAlbums(); } }}>Rename</button>
            <button onClick={async () => { if (confirm('Delete album?')) { await fetch(`${API_BASE}/albums/${albumId}`, { method: 'DELETE' }); setAlbumId(''); await refreshAlbums(); } }}>Delete</button>
          </>
        )}
      </div>

      <section style={{ marginBottom: 24, padding: 16, border: '1px solid #e5e7eb', borderRadius: 8 }}>
        <h3>Ask My Screenshots</h3>
        <form onSubmit={handleAsk} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 12 }}>
          <input
            type="text"
            placeholder="What's my booking reference for Bali?"
            value={askQuestion}
            onChange={(e) => setAskQuestion(e.target.value)}
            style={{ flex: 1, padding: 8 }}
          />
          <button type="submit" disabled={!askQuestion.trim()}>Ask</button>
        </form>
        {askAnswer && (
          <div style={{ background: '#f9fafb', padding: 12, borderRadius: 6 }}>
            <p><strong>Answer:</strong> {askAnswer.answer}</p>
            {askAnswer.citations.length > 0 && (
              <div>
                <strong>Sources:</strong>
                {askAnswer.citations.map((c, i) => (
                  <div key={i} style={{ marginTop: 8, padding: 8, background: 'white', borderRadius: 4 }}>
                    <button onClick={() => setDetailId(c.image_id)} style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', textDecoration: 'underline' }}>
                      {c.filename}
                    </button>
                    <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>{c.text_snippet}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      {error && <div style={{ color: 'crimson', marginBottom: 12 }}>{error}</div>}

      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
        {results.map(r => (
          <figure key={r.id} style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 8 }}>
            <img
              alt={r.filename}
              src={`${API_BASE.replace(/\/$/, '')}/${r.image_path}`}
              style={{ width: '100%', height: 180, objectFit: 'cover', borderRadius: 6 }}
              onClick={() => setDetailId(r.id)}
            />
            <figcaption style={{ fontSize: 12, marginTop: 6 }}>
              <strong>{r.filename}</strong>
              <div title={r.text} style={{ color: '#4b5563', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.text}</div>
              <div style={{ color: '#6b7280' }}>type: {r as any && (r as any).type_label ? (r as any).type_label : '—'} · score: {r.score.toFixed(3)}</div>
              {r.entities && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
                  {Object.entries(r.entities).slice(0, 4).map(([t, vals]) => (
                    <span key={t} style={{ background: '#f3f4f6', padding: '2px 6px', borderRadius: 999, fontSize: 11 }}>
                      {t}: {vals[0]}
                    </span>
                  ))}
                </div>
              )}
            </figcaption>
          </figure>
        ))}
      </section>
      {detailId && (
        <ImageDetail
          apiBase={API_BASE}
          imageId={detailId}
          src={`${API_BASE.replace(/\/$/, '')}/images/${detailId}.jpg`}
          onClose={() => setDetailId(null)}
          highlight={query}
          entities={results.find(r => r.id === detailId)?.entities}
        />
      )}
    </div>
  )
}


