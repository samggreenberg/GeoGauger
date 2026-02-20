import { useState } from 'react'
import './App.css'

interface LocationMatch {
  city: string
  state: string | null
  country: string
  latitude: number
  longitude: number
  matching_streets: string[]
  match_count: number
  total_queried: number
}

function App() {
  const [streetInput, setStreetInput] = useState('')
  const [results, setResults] = useState<LocationMatch[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    const streets = streetInput
      .split('\n')
      .map((s) => s.trim())
      .filter((s) => s.length > 0)

    if (streets.length === 0) {
      setError('Please enter at least one street name.')
      return
    }

    setLoading(true)
    setError(null)
    setResults([])

    try {
      const response = await fetch('/api/locate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ street_names: streets }),
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data: LocationMatch[] = await response.json()
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header>
        <h1>GeoGauger</h1>
        <p>Enter street names near you to find where you might be.</p>
      </header>

      <main>
        <section className="search-section">
          <label htmlFor="street-input">Street names (one per line):</label>
          <textarea
            id="street-input"
            value={streetInput}
            onChange={(e) => setStreetInput(e.target.value)}
            placeholder={'Main Street\nOak Avenue\nElm Drive'}
            rows={6}
          />
          <button onClick={handleSearch} disabled={loading}>
            {loading ? 'Searching...' : 'Find Location'}
          </button>
        </section>

        {error && <p className="error">{error}</p>}

        {results.length > 0 && (
          <section className="results-section">
            <h2>Possible Locations</h2>
            <ul className="results-list">
              {results.map((match, i) => (
                <li key={i} className="result-card">
                  <h3>
                    {match.city}
                    {match.state ? `, ${match.state}` : ''}, {match.country}
                  </h3>
                  <p className="coords">
                    {match.latitude.toFixed(4)}, {match.longitude.toFixed(4)}
                  </p>
                  <p className="match-info">
                    {match.match_count} of {match.total_queried} streets matched
                  </p>
                  <p className="matching-streets">
                    Matched: {match.matching_streets.join(', ')}
                  </p>
                </li>
              ))}
            </ul>
          </section>
        )}

        {results.length === 0 && !loading && !error && streetInput.trim() && (
          <p className="no-results">No results yet. Click "Find Location" to search.</p>
        )}
      </main>
    </div>
  )
}

export default App
