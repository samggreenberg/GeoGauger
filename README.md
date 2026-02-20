# GeoGauger

A geolocation tool that identifies where you might be based on nearby street names. Enter the names of streets around you, and GeoGauger will search its database to find matching locations.

## Quick Start

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

## How It Works

1. Enter one or more street names (one per line)
2. GeoGauger searches its database for locations that contain those streets
3. Results are ranked by how many of your queried streets match each location
4. The best matches (most streets in common) appear first

## Development

Run tests:

```bash
# Backend
cd backend && python -m pytest

# Frontend
cd frontend && npm test
```

Run linters:

```bash
# Backend
cd backend && ruff check .

# Frontend
cd frontend && npm run lint
```
