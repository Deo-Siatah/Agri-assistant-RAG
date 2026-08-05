import { useEffect, useState } from 'react'
import { MapPin, Leaf, RefreshCw } from 'lucide-react'

import ChatPanel from './components/ChatPanel'
import LocationSearch from './components/LocationSearch'
import type { County } from './data/kenyaCounties'

export default function App() {
  const [county, setCounty] = useState<County | null>(null)
  const [view, setView] = useState<'select-county' | 'chat'>('select-county')

  useEffect(() => {
    const storedCounty = localStorage.getItem('agri_selected_county')

    if (!storedCounty) {
      return
    }

    try {
      const parsedCounty = JSON.parse(storedCounty) as County
      setCounty(parsedCounty)
      setView('chat')
    } catch {
      localStorage.removeItem('agri_selected_county')
    }
  }, [])

  const handleCountySelect = (selectedCounty: County) => {
    setCounty(selectedCounty)
    localStorage.setItem('agri_selected_county', JSON.stringify(selectedCounty))
    setView('chat')
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {
          --primary: #0F172A;
          --primary-hover: #1E293B;
          --surface: #FFFFFF;
          --background: #F8FAFC;
          --border: #E2E8F0;
          --text-main: #0F172A;
          --text-muted: #64748B;
          --accent: #10B981;
          --radius-lg: 24px;
        }

        body {
          margin: 0;
          background: var(--background);
          -webkit-font-smoothing: antialiased;
        }

        .app-layout {
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
          min-height: 100dvh;
          display: flex;
          flex-direction: column;
          align-items: center;
          background: var(--background);
          color: var(--text-main);
        }

        .app-navbar {
          width: 100%;
          padding: 1.25rem 1.5rem;
          display: flex;
          justify-content: center;
          background: var(--surface);
          border-bottom: 1px solid var(--border);
          box-shadow: 0 4px 20px -10px rgba(0, 0, 0, 0.05);
          position: sticky;
          top: 0;
          z-index: 50;
        }

        .brand-container {
          width: 100%;
          max-width: 900px;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .brand-icon {
          background: rgba(16, 185, 129, 0.1);
          color: var(--accent);
          padding: 8px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .brand-title {
          font-weight: 700;
          font-size: 1.125rem;
          letter-spacing: -0.02em;
          color: var(--primary);
          margin: 0;
        }

        .main-content {
          width: 100%;
          max-width: 900px;
          flex-grow: 1;
          display: flex;
          flex-direction: column;
          padding: 1.5rem;
          gap: 1.5rem;
        }

        /* Location Bar Styles */
        .location-bar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 16px;
          padding: 12px 20px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
        }

        .location-info {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 500;
          color: var(--text-main);
        }

        .location-icon {
          color: var(--accent);
        }

        .change-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          background: var(--background);
          border: 1px solid var(--border);
          color: var(--text-muted);
          font-family: inherit;
          font-weight: 500;
          font-size: 0.875rem;
          padding: 8px 16px;
          border-radius: 10px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .change-btn:hover {
          background: var(--surface);
          color: var(--primary);
          border-color: var(--text-muted);
          box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }

        /* Ensure ChatPanel integrates beautifully */
        .chat-view-wrapper {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          height: 100%;
          flex-grow: 1;
        }

        @media (max-width: 768px) {
          .main-content {
            padding: 1rem;
          }
          
          .app-navbar {
            padding: 1rem;
          }

          .location-bar {
            padding: 12px 16px;
          }
        }
      `}</style>

      <div className="app-layout">
        <nav className="app-navbar">
          <div className="brand-container">
            <div className="brand-icon">
              <Leaf size={22} strokeWidth={2.5} />
            </div>
            <h1 className="brand-title">Agri Assistant</h1>
          </div>
        </nav>

        <main className="main-content">
          {view === 'select-county' ? (
            <LocationSearch selected={county} onSelect={handleCountySelect} />
          ) : (
            <div className="chat-view-wrapper">
              <div className="location-bar">
                <div className="location-info">
                  <MapPin size={18} className="location-icon" />
                  <span>{county?.name ?? 'Unknown county'}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setView('select-county')}
                  className="change-btn"
                >
                  <RefreshCw size={14} />
                  Change Area
                </button>
              </div>

              <ChatPanel selectedCounty={county} />
            </div>
          )}
        </main>
      </div>
    </>
  )
}