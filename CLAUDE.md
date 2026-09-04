<!-- //// Neoffice - added file (no upstream equivalent). Working notes for this fork
     //// (bc9617b4e + 7d62dc723, 2026-05-07/2026-05-11): the commit-the-build pipeline and the Frappe
     //// Shell Native integration, both of which are ours. TO REVIEW: parts of it are written in
     //// French; code and docs in this repo are supposed to be English. -->
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
| `build.yml` | Manual/releases | Docker image build |

**Note**: Frontend assets must be built on the server using `bench build --app raven`.

## Build pipeline (commit-the-build)

⚠️ **Ne jamais lancer `yarn build` ou `bench build --app Raven` localement sur un serveur Neoffice** (4 GB RAM → OOM-kill garanti). Le build se fait UNIQUEMENT sur GitHub Actions (ubuntu-latest, 16 GB RAM).

### Comment ça marche

1. Modif d'un fichier source (`frontend/...`) en local → `git commit` → `git push origin version-15`. **Ne pas builder localement.**
2. Le workflow `.github/workflows/build-frontend.yml` détecte le push, lance `yarn build` sur ubuntu-latest (~1-2 min) et commit les artefacts back avec un commit `[skip-build] frontend artifacts for <SHA>` (par `github-actions[bot]`).
3. Sur les instances clients, le pipeline d'update fait `git pull` (ramène ton commit + le commit du bot). Quand `bench build --app Raven` tourne, il appelle `yarn build` à la racine — **le `package.json` voit les artefacts déjà présents et skip vite** (gate). Plus d'OOM-kill.

### Paths spécifiques

- **Source frontend** : `frontend/`
- **Artefacts vite (commités)** : `raven/public/raven/`
- **SPA HTML(s) (commités)** : `raven/www/raven.html`
- **Build script root** : `yarn workspace (root → frontend, `--base=/assets/raven/raven/`)`

### Forcer un rebuild local (si vraiment nécessaire)

```bash
FORCE_REBUILD=1 yarn build
```

### Documentation complète

- Doc canonique : `bvisible/neoffice-devops:main` → `docs/COMMIT-BUILD-PATTERN.md`
- Doc batch migration (12 apps) : même fichier, sections "Apps that have adopted the pattern" + "Edge cases discovered"
- Vault Obsidian : `[[NORA/04-savoir-faire/drive-frontend-build-pattern]]`

### Edge cases spécifiques à Raven

- ⚠️ Path atypique : artefacts dans `raven/public/raven/` (pas `public/frontend/`).
- ⚠️ `bvisible/Raven` avait tous les workflows GH Actions `disabled_manually`. Réactiver avec `gh workflow enable build-frontend -R bvisible/Raven` si besoin.
- ⚠️ **Le workflow CI doit passer `FORCE_REBUILD=1`** (`env: FORCE_REBUILD: '1'` dans le step Build de `.github/workflows/build-frontend.yml`). Sinon le guard `package.json` (qui protège les instances 4 GB d'OOM-kill) SKIPpe le build CI parce que `raven/public/raven/assets` est déjà présent dans le checkout. Symptôme dans les logs : `[skip-build] pre-built artifacts present` au lieu de `vite v6 building for production`. Bug rencontré 2026-05-11 lors de l'intégration Frappe Shell Native (commits `0d9040e` + `d483fb0`).
- `raven_v3` reste dans `.gitignore` : pas de build pour cette variante aujourd'hui.

## Frappe Shell Native (chrome embarqué dans /raven)

Depuis 2026-05-11, `/raven` rend le **même chrome que `/app/home`** (sidebar Frappe collapsée 50px avec hover-expand + app-switcher, navbar Frappe avec logo neoffice + search + horloge + calendar + notifs + Aide + user) tout en préservant l'UX Raven existante (workspaces + channels + chat). C'est l'application du [pattern Frappe Shell Native](https://github.com/bvisible/Raven/blob/version-15/raven/api/boot.py) commun à Mint et Neoconstruction.

### Comment ça marche

1. `raven/hooks.py` déclare `required_apps = ["neoffice_theme"]` (sprite Lucide + `neoffice-theme.css` + DocType `App Customization`).
2. `raven/api/boot.py` expose un **mini-boot curaté** (`get_navbar_boot()`, ~28 keys) qui inclut `docs`, `sidebar_pages`, `app_data`, et bake les UI translations dans `__messages` (sinon menu en EN forcé).
3. `raven/www/raven.py` sert ce mini-boot au lieu du `frappe.sessions.get()` complet et expose `desk_css_url` + `neoffice_theme_css_url` via `bundled_asset()`.
4. `frontend/index.html` (la SOURCE Vite, copiée vers `raven/www/raven.html` post-build via `yarn copy-html-entry`) charge `desk.bundle.css` + `neoffice-theme.css`, installe le shim `window['__']` (i18n minimaliste), pose `window['__FRAPPE_INTEGRATION__'] = true`, et inline 3 sprites SVG (timeless + espresso + lucide).
5. `frontend/src/components/layout/frappe/{FrappeSidebar,FrappeNavbar,FrappeLayout,i18n}.tsx` reproduisent le DOM exact de `frappe/public/js/frappe/ui/{sidebar,navbar,apps_switcher}.html`. Toutes les strings hardcoded sont wrappées dans `t()`.
6. `frontend/src/utils/auth/ProtectedRoute.tsx` wrappe l'`<Outlet />` authentifié dans `<FrappeLayout>` quand `__FRAPPE_INTEGRATION__` est true. Les routes `/login`, `/signup`, `/forgot-password` restent en plein écran.
7. `frontend/src/components/layout/Sidebar/Sidebar.tsx` retire conditionnellement `<FrappeSidebar fixed={false}>` du package npm `@neoffice/frappe-sidebar-react` quand l'integration est ON (sinon doublon visuel 100px à gauche).

### Pièges importants

- **Bracket notation OBLIGATOIRE** dans `frontend/index.html` pour tout ce qui contient `__` : `window['__']`, `window['__FRAPPE_INTEGRATION__']`, `window['__FRAPPE_BASENAME__']`. Frappe `safe_render` Jinja rejette tout substring `.__` (anti-SSTI), commentaires JS inclus → HTTP 417 Illegal Template, page entière cassée.
- **`docs` doit être dans `NAVBAR_BOOT_KEYS`** sinon le `safeSyncDocs()` no-op et certains scripts third-party plantent en lisant `frappe.boot.docs.<x>`.
- **Workflow CI = `FORCE_REBUILD=1`** (cf. edge case ci-dessus).
- **`.page-content` a `padding: 0`** (différent de Mint qui utilise `24px 36px`). Le chat Raven prend tout le viewport, l'overflow est géré par les composants Raven internes.
- **Toute modif HTML doit aller dans `frontend/index.html`**, pas dans `raven/www/raven.html` (sinon écrasée au prochain build par `copy-html-entry`).

### Documentation complète

- Pattern transversal : Vault Obsidian → `Neoffice/Frappe-Shell-Native-Pattern.md` (13 pièges détaillés, playbook 9 étapes, variantes par app)
- Session log Raven : Vault Obsidian → `wiki/log.md` entrée `[2026-05-11] raven | Frappe Shell Native intégré`
- Apps adoptantes : Neoconstruction (2026-04-25), Mint (2026-05-11), Raven (2026-05-11)
