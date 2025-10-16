import React from 'react'
import SmartActions from './SmartActions'

type OCRBlock = { text: string; conf: number; bbox: { x: number; y: number; w: number; h: number } }

export default function ImageDetail({ apiBase, imageId, src, onClose, highlight, entities }: { apiBase: string; imageId: string; src: string; onClose: () => void; highlight?: string; entities?: Record<string, string[]> }) {
  const [blocks, setBlocks] = React.useState<OCRBlock[]>([])
  const [entityIdxs, setEntityIdxs] = React.useState<Record<string, number[]>>({})
  const [activeEntity, setActiveEntity] = React.useState<string>('')
  const [loaded, setLoaded] = React.useState(false)
  const imgRef = React.useRef<HTMLImageElement>(null)

  React.useEffect(() => {
    fetch(`${apiBase}/image/${imageId}/ocr`).then(r => r.json()).then(d => { setBlocks(d.blocks || []); setEntityIdxs(d.entity_block_idxs || {}) }).catch(() => { setBlocks([]); setEntityIdxs({}) })
  }, [apiBase, imageId])

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ position: 'relative', background: 'white', padding: 12 }}>
        <button onClick={onClose} style={{ position: 'absolute', right: 8, top: 8 }}>Close</button>
        <div style={{ position: 'relative' }}>
          <img ref={imgRef} src={src} alt="detail" onLoad={() => setLoaded(true)} style={{ maxWidth: '80vw', maxHeight: '70vh' }} />
          {loaded && imgRef.current && (
            <Overlay img={imgRef.current} blocks={blocks} highlight={highlight} activeEntity={activeEntity} entityIdxs={entityIdxs} />
          )}
        </div>
        {entities && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
            {Object.entries(entities).slice(0, 8).map(([t, vals]) => {
              const isActive = activeEntity === t
              return (
                <button key={t} onClick={() => setActiveEntity(isActive ? '' : t)} style={{ background: isActive ? '#c7d2fe' : '#eef2ff', padding: '2px 6px', borderRadius: 999, fontSize: 12, border: 0 }}>
                  {t}: {vals[0]}
                </button>
              )
            })}
          </div>
        )}
        <SmartActions entities={entities} />
      </div>
    </div>
  )
}

function Overlay({ img, blocks, highlight, activeEntity, entityIdxs }: { img: HTMLImageElement; blocks: OCRBlock[]; highlight?: string; activeEntity?: string; entityIdxs?: Record<string, number[]> }) {
  const naturalW = img.naturalWidth
  const naturalH = img.naturalHeight
  const rect = img.getBoundingClientRect()
  const scaleX = rect.width / naturalW
  const scaleY = rect.height / naturalH
  const hl = (highlight || '').trim().toLowerCase()
  const activeSet = new Set((activeEntity && entityIdxs && entityIdxs[activeEntity]) ? entityIdxs[activeEntity] : [])
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: rect.width, height: rect.height, pointerEvents: 'none' }}>
      {blocks.map((b, i) => {
        const byText = hl && b.text.toLowerCase().includes(hl)
        const byEntity = activeSet.has(i)
        const border = byEntity ? '2px solid rgba(59,130,246,0.9)' : byText ? '2px solid rgba(34,197,94,0.9)' : '1px solid rgba(255,0,0,0.6)'
        return <div key={i} style={{
          position: 'absolute',
          left: b.bbox.x * scaleX,
          top: b.bbox.y * scaleY,
          width: b.bbox.w * scaleX,
          height: b.bbox.h * scaleY,
          border
        }} title={`${b.text} (${b.conf.toFixed(0)})`} />
      })}
    </div>
  )
}


