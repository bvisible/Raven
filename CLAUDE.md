# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Synk** (codebase: Raven) is an open-source enterprise messaging platform built on the Frappe Framework. It provides channels, direct messages, threads, reactions, AI agents, and deep integrations with ERPNext and FrappeHR.

> **Branding**: The app is published as "Synk" but the codebase uses "raven" for module names, paths, and identifiers.

## Development Commands

### Prerequisites
Raven requires a Frappe bench environment. Set up with:
```bash
bench set-config -g developer_mode 1
bench --site <site> set-config ignore_csrf 1
```

### Backend (Python/Frappe)
```bash
# Run all tests
bench --site <site> run-tests --app raven

# Run a specific test file
bench --site <site> run-tests --app raven --module raven.tests.test_permissions

# Run a specific test class/method
bench --site <site> run-tests --app raven --doctype "Raven Message"

# Start development server
bench start
```

### Frontend (React/Vite)
```bash
# Install dependencies (from repo root)
yarn install

# Start development server with hot reload (http://localhost:8080)
yarn dev
# Or from frontend directory:
cd frontend && yarn dev

# Build for production (skips if assets exist)
yarn build

# Force rebuild (ignores existing assets)
cd frontend && yarn build:force
```

**Build output**: Assets are compiled to `raven/public/raven/` and `raven/www/raven.html`

### Mobile App (React Native/Expo)
```bash
# From apps/mobile directory
yarn start           # Start Expo dev server
yarn ios             # Run on iOS simulator
yarn android         # Run on Android emulator
yarn nuke            # Clean all build artifacts
```

### Linting and Pre-commit
```bash
# Run pre-commit hooks
pre-commit run --all-files

# Python formatting (black, isort, flake8)
black raven/
isort raven/

# Run semgrep security checks
semgrep ci --config ./frappe-semgrep-rules/rules
```

## Architecture

### Monorepo Structure
- **`raven/`** - Frappe app (Python backend)
  - `api/` - API endpoints (whitelisted methods)
  - `raven/` - Core module (users, workspaces, settings)
  - `raven_messaging/` - Messages, reactions, polls, mentions
  - `raven_channel_management/` - Channels and members
  - `raven_bot/` - Bot framework
  - `raven_ai/` - AI functions and prompts
  - `raven_integrations/` - ERPNext/FrappeHR integrations, webhooks, scheduler
  - `hooks.py` - Frappe hooks (doc_events, scheduler, permissions)
  - `permissions.py` - Permission query conditions and has_permission checks

- **`frontend/`** - Web app (React + Vite + TailwindCSS)
  - `src/components/feature/` - Feature-specific components (chat, channels, ai, etc.)
  - `src/pages/` - Route pages
  - `src/hooks/` - Custom React hooks
  - Uses RadixUI for UI components, TipTap for rich text editing

- **`apps/mobile/`** - Mobile app (React Native + Expo)
  - Uses NativeWind (TailwindCSS), React Native Reanimated

- **`packages/`** - Shared packages
  - `lib/` - Shared React hooks and utilities (`@raven/lib`)
  - `types/` - TypeScript type definitions (`@raven/types`)

### Key Patterns

**Frappe DocTypes**: Backend models are Frappe DocTypes located in `raven/<module>/doctype/`. Each doctype has:
- `<doctype>.json` - Schema definition
- `<doctype>.py` - Python controller
- `test_<doctype>.py` - Test file

**API Endpoints**: Whitelisted methods in `raven/api/` are called via Frappe's `/api/method/` route.

**Real-time Updates**: Uses Frappe's socket.io integration for live messaging.

**Permissions**: Custom permission logic in `raven/permissions.py` controls access to channels, messages, and workspaces based on membership.

### Frontend Environment
Create `frontend/.env.local` for local development:
```
VITE_BASE_NAME=''
VITE_SOCKET_PORT=9000
VITE_SITE_NAME='raven.test'
```

## Code Style

- Python: Black (99 char line length), isort, flake8
- TypeScript/React: Standard Vite/React patterns
- TailwindCSS for styling across web and mobile

## CI/CD (GitHub Actions)

Workflows in `.github/workflows/`:

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `ci.yml` | Push/PR on `main` (raven/** paths) | Runs Python tests with MariaDB/Redis |
| `linters.yml` | Push/PR on `main` (raven/** paths) | Pre-commit hooks + Semgrep security |
| `build-frontend.yml` | Push on `develop`/`main` (frontend/** paths) | Auto-builds and commits frontend assets |
| `build.yml` | Manual/releases | Docker image build |

**Auto-build**: When frontend files change on `develop` or `main`, GitHub Actions automatically rebuilds assets and commits them with `[skip ci]`.
