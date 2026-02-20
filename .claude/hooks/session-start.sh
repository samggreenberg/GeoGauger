#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install backend Python dependencies
cd "$CLAUDE_PROJECT_DIR/backend"
pip install -e ".[dev]" --quiet

# Install frontend Node dependencies
cd "$CLAUDE_PROJECT_DIR/frontend"
npm install
