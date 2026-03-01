# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal banking analytics app for importing transaction history from banks (Belfius, ING, MasterCard), categorizing transactions (with ML-assisted tagging and tag rules), and analyzing expenses via dashboards. Multi-user with JWT auth. Dockerized deployment.

## Architecture

There are two versions of the app in this repo:
- **v1 (legacy)**: Flask + Vue 2 — `server/` and `frontend/`. Still deployed but no longer actively developed.
- **v2 (active)**: FastAPI + Vue 3 — `v2/backend/` and `v2/frontend/`. This is where all new work happens.

### v2 Backend (`v2/backend/`)

FastAPI app with SQLAlchemy 2.0 ORM, Alembic migrations, python-jose for JWT.

- `app/main.py` — App entry, lifespan, router mounting
- `app/config.py` — Settings via env vars (prefix: `BANKING_`)
- `app/routers/` — API endpoints: `auth`, `accounts`, `categories`, `currencies`, `imports`, `ml`, `tag_rules`, `transactions`, `transaction_groups`, `wallets`, `wallet_stats`
- `app/models/` — SQLAlchemy models: `User`, `Account`, `Category` (hierarchical), `CategorySplit` (dual FK: transaction or group), `Currency`, `Transaction`, `TransactionGroup`, `Wallet`, `WalletAccount`, `TagRule`, `ImportRecord`, `MLModel`, `RecurringPattern`, `ExpenseSplit`, `AccountAlias`
- `app/services/` — Business logic: `import_service` (parsing, dedup, auto-tag), `tag_rule_service` (rule matching)
- `app/parsers/` — Bank-specific parsers: `belfius` (CSV), `ing` (CSV), `mastercard` (PDF)
- `app/schemas/` — Pydantic request/response models
- `app/migrations/versions/` — Alembic migration files
- `tests/` — pytest tests (SQLite in-memory, no running DB needed)

**API prefix**: `/api/v2/`
**Auth**: JWT access token in Authorization header, refresh token in httpOnly cookie
**Database**: PostgreSQL (`banking_v2`)

### v2 Frontend (`v2/frontend/`)

Vue 3 + Vite + PrimeVue 4 + Tailwind CSS + Pinia stores.

- `src/views/` — Page components: WalletTabView (dashboard), TransactionFlowView, ReviewInboxView, ImportView, ImportDetailView, SettingsView, SwipeTaggerView, HelpView, CategoryTransactionsView, TransactionDetailView
- `src/components/` — Organized by feature: `analytics/`, `flow/`, `imports/`, `settings/`, `tagger/`, `transactions/`, `wallets/`, `common/`, `layout/`
- `src/stores/` — Pinia stores: auth, wallets, activeWallet, categories, transactions, transactionFlow, imports
- `src/composables/` — Reusable composition functions: `useInfiniteScroll`
- `src/i18n/index.js` — EN/FR translations (inline, no CSV)
- `src/router/index.js` — Vue Router routes

## Key Data Model Concepts

- **Wallet**: Groups accounts for analysis. Income = money entering wallet from outside; expense = money leaving. Internal transfers excluded from stats.
- **Transaction Group**: Links related transactions (payment + reimbursements). Has its own `CategorySplit` entries. Net expense = total paid − total reimbursed. In stats, groups are treated as single entities (individual member transactions excluded from per-category stats).
- **CategorySplit**: Dual FK — belongs to either a `Transaction` (via `id_transaction`) or a `TransactionGroup` (via `id_group`). Stores amount per category.
- **effective_amount**: On Transaction, stores the wallet-relative share after group computation. Outgoing transactions get reduced amounts; incoming reimbursements get 0.
- **Duplicate detection**: Matches on (source, dest, date, amount). Duplicates kept in DB with `id_duplicate_of` set, excluded from stats/lists.
- **auto_tagged_at_import**: Boolean on Transaction, persists whether the transaction was auto-tagged during import (frozen-in-time view).

## Common Commands

### v2 Backend
```bash
cd v2/backend
poetry run pytest tests/                        # Run all tests (SQLite, no DB needed)
poetry run pytest tests/test_imports.py -v       # Single test file
PYTHONPATH=. poetry run alembic revision --autogenerate -m "msg"  # Generate migration (needs running PostgreSQL)
PYTHONPATH=. poetry run alembic upgrade head     # Apply migrations
```

### v2 Frontend
```bash
cd v2/frontend
npm install
npm run dev           # Vite dev server
npm run build         # Production build
npx vitest run        # Run all tests
```

### v1 Legacy Backend (server/)
```bash
python -m pytest                          # Run all tests
python -m flask run --debug               # Dev server
./scripts/dev-up.sh                       # Start dev Docker environment
./scripts/dev-down.sh                     # Stop dev Docker environment
```

### v1 Legacy Frontend (frontend/)
```bash
yarn install && yarn serve    # Dev server
yarn build                    # Production build
```

### Production
```bash
docker compose pull && docker compose up -d
```

## Testing Requirements

- **Always run tests** after making changes: backend (`poetry run pytest tests/`) and frontend (`npx vitest run`)
- Backend tests use SQLite in-memory — no running PostgreSQL needed
- Test files are in `v2/backend/tests/` with shared fixtures in `conftest.py`
- Helpers available in conftest: `categorize()`, `create_group()`, `categorize_group()`

## Key Technical Details

- **v1 → v2 renames**: `Group` → `Wallet`, `AccountGroup` → `WalletAccount`, `custom_id` → `external_id`, `when` → `date`, `password` → `password_hash`, `MLModelFile` → `MLModel`
- **Icons**: FontAwesome Free solid icons in `"fas fa-xxx"` format
- **i18n**: Inline EN/FR in `v2/frontend/src/i18n/index.js`
- **ML training**: Requires ≥50 labeled transactions; model stored in DB
- **Environment**: Config via env vars with `BANKING_` prefix
