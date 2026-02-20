import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders the heading', () => {
    render(<App />)
    expect(screen.getByText('GeoGauger')).toBeInTheDocument()
  })

  it('renders the search textarea', () => {
    render(<App />)
    expect(screen.getByLabelText(/street names/i)).toBeInTheDocument()
  })

  it('renders the search button', () => {
    render(<App />)
    expect(screen.getByRole('button', { name: /find location/i })).toBeInTheDocument()
  })
})
