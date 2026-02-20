# GeoGauger - Claude Code Guide

## Project Overview
GeoGauger is a geolocation tool where users enter nearby street names and the app identifies possible locations. It uses a database of street names mapped to geographic coordinates.

## Tech Stack
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, SQLite
- **Frontend**: React 19, TypeScript, Vite
- **Testing**: pytest (backend), vitest (frontend)
- **Linting**: ruff (backend), eslint (frontend)

## Project Structure
```
backend/          Python FastAPI backend
  app/            Application code
    main.py       FastAPI app entry point
    models.py     SQLAlchemy models and DB setup
    schemas.py    Pydantic request/response schemas
    routes.py     API route handlers
  tests/          Backend tests
  pyproject.toml  Python project config
frontend/         React + Vite frontend
  src/            Source code
  package.json    Node project config
```

## Commands

### Backend
```bash
# Install dependencies (from backend/)
cd backend && pip install -e ".[dev]"

# Run server
cd backend && uvicorn app.main:app --reload

# Run tests
cd backend && python -m pytest

# Lint
cd backend && ruff check .

# Format
cd backend && ruff format .
```

### Frontend
```bash
# Install dependencies (from frontend/)
cd frontend && npm install

# Run dev server
cd frontend && npm run dev

# Run tests
cd frontend && npm test

# Lint
cd frontend && npm run lint

# Build
cd frontend && npm run build
```

## API Endpoints
- `GET /health` - Health check
- `POST /api/locate` - Find locations matching street names
- `POST /api/streets` - Add a street location to the database
- `GET /api/streets` - List all street locations

## Conventions
- Backend code uses ruff for linting and formatting (line length 100)
- Frontend uses ESLint with TypeScript rules
- All API routes are prefixed with `/api`
- Backend tests use pytest with the test database `test_geogauger.db`
- Frontend dev server proxies `/api` requests to the backend at `localhost:8000`

## Permissions
Claude has full auto-approval for all actions on this project.
