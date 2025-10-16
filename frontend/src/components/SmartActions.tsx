import React from 'react'

export default function SmartActions({ entities }: { entities?: Record<string, string[]> }) {
  if (!entities) return null
  const url = entities.url?.[0]
  const email = entities.email?.[0]
  const phone = entities.phone?.[0]
  const dateRaw = entities.date?.[0]
  const calLink = buildCalendarLink(dateRaw)

  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
      {url && <a href={url} target="_blank" rel="noreferrer" style={btn}>Open Link</a>}
      {email && <a href={`mailto:${email}`} style={btn}>Email</a>}
      {phone && <a href={`tel:${phone.replace(/[^+\d]/g,'')}`} style={btn}>Call</a>}
      {calLink && <a href={calLink} target="_blank" rel="noreferrer" style={btn}>Add to Calendar</a>}
      {/* Calendar deep-link is mocked; real impl would parse date/time to RFC3339 */}
    </div>
  )
}

const btn: React.CSSProperties = { background: '#e5e7eb', padding: '6px 10px', borderRadius: 6, textDecoration: 'none', color: '#111827', fontSize: 12 }

function buildCalendarLink(dateRaw?: string): string | null {
  if (!dateRaw) return null
  // Try parse patterns like "22 Nov 2025 3:30 PM" or "11/22/2025 15:30"
  const d = parseLooseDate(dateRaw)
  if (!d) return null
  const start = toGCalDateTime(d)
  const end = toGCalDateTime(new Date(d.getTime() + 60 * 60 * 1000))
  return `https://calendar.google.com/calendar/u/0/r/eventedit?text=Event&dates=${start}/${end}`
}

function parseLooseDate(s: string): Date | null {
  const m1 = s.match(/(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})(?:\s+(\d{1,2}):(\d{2})\s*(AM|PM)?)?/i)
  if (m1) {
    const day = parseInt(m1[1], 10)
    const mon = monthIndex(m1[2])
    const year = parseInt(m1[3], 10)
    let hour = m1[4] ? parseInt(m1[4], 10) : 9
    const minute = m1[5] ? parseInt(m1[5], 10) : 0
    const ampm = (m1[6] || '').toUpperCase()
    if (ampm === 'PM' && hour < 12) hour += 12
    if (ampm === 'AM' && hour === 12) hour = 0
    if (mon >= 0) return new Date(year, mon, day, hour, minute)
  }
  const m2 = s.match(/(\d{1,2})\/(\d{1,2})\/(\d{2,4})(?:\s+(\d{1,2}):(\d{2}))?/)
  if (m2) {
    const mm = parseInt(m2[1], 10) - 1
    const dd = parseInt(m2[2], 10)
    const yy = parseInt(m2[3].length === 2 ? `20${m2[3]}` : m2[3], 10)
    const hour = m2[4] ? parseInt(m2[4], 10) : 9
    const minute = m2[5] ? parseInt(m2[5], 10) : 0
    return new Date(yy, mm, dd, hour, minute)
  }
  return null
}

function monthIndex(mon: string): number {
  const arr = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
  const i = arr.indexOf(mon.slice(0,3).toLowerCase())
  return i
}

function toGCalDateTime(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  // Use local timezone offset instead of Z (UTC)
  const offset = d.getTimezoneOffset()
  const offsetHours = Math.floor(Math.abs(offset) / 60)
  const offsetMinutes = Math.abs(offset) % 60
  const offsetSign = offset <= 0 ? '+' : '-'
  const offsetStr = `${offsetSign}${String(offsetHours).padStart(2, '0')}:${String(offsetMinutes).padStart(2, '0')}`
  return `${y}${m}${day}T${hh}${mm}00${offsetStr}`
}


