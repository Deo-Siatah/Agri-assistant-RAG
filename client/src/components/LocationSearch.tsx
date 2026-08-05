import { useEffect, useMemo, useRef, useState } from 'react'
import { MapPin } from 'lucide-react'

import { KENYA_COUNTIES, type County } from '../data/kenyaCounties'

type LocationSearchProps = {
  onSelect: (county: County) => void
  selected: County | null
}

const LocationSearch = ({ onSelect, selected }: LocationSearchProps) => {
  const [query, setQuery] = useState(selected?.name ?? '')
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    setQuery(selected?.name ?? '')
  }, [selected])

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handlePointerDown)
    return () => document.removeEventListener('mousedown', handlePointerDown)
  }, [])

  const matches = useMemo(() => {
    const search = query.trim().toLowerCase()

    if (!search) {
      return KENYA_COUNTIES.slice(0, 8)
    }

    return KENYA_COUNTIES.filter((county) => county.name.toLowerCase().includes(search)).slice(0, 8)
  }, [query])

  const handleSelect = (county: County) => {
    setQuery(county.name)
    setOpen(false)
    onSelect(county)
  }

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%', maxWidth: 420 }}>
      <div style={{ position: 'relative' }}>
        <MapPin
          size={16}
          aria-hidden="true"
          style={{
            position: 'absolute',
            left: 'var(--spacing-3)',
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--color-text-muted)',
            pointerEvents: 'none',
          }}
        />
        <input
          type="text"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value)
            setOpen(true)
          }}
          onFocus={() => setOpen(true)}
          placeholder="Search county"
          style={{
            width: '100%',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--color-surface)',
            color: 'var(--color-text)',
            fontFamily: 'var(--font-sans)',
            fontSize: 16,
            lineHeight: 1.5,
            padding: 'var(--spacing-2) var(--spacing-3) var(--spacing-2) calc(var(--spacing-3) + 20px)',
            outline: 'none',
          }}
        />
      </div>

      {open && matches.length > 0 ? (
        <div
          role="listbox"
          style={{
            position: 'absolute',
            zIndex: 10,
            top: 'calc(100% + 6px)',
            left: 0,
            right: 0,
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
            overflow: 'hidden',
          }}
        >
          {matches.map((county) => (
            <button
              key={county.name}
              type="button"
              onClick={() => handleSelect(county)}
              style={{
                width: '100%',
                textAlign: 'left',
                background: 'transparent',
                border: 'none',
                padding: 'var(--spacing-2) var(--spacing-3)',
                fontFamily: 'var(--font-sans)',
                fontSize: 14,
                color: 'var(--color-text)',
                cursor: 'pointer',
              }}
            >
              {county.name}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}

export default LocationSearch