# reapersJournal — Architecture & Change-Impact Plan

Local-only, self-hosted trading journal. Phase 1 = Forex. Built to widen to Indian Equity / Futures / Options / Crypto without rewrites.

Stack (same as shadowDebt): React + Vite · FastAPI (Python 3.12) · PostgreSQL 16 · Docker Compose (5 services) · Nginx reverse proxy · deployed from GitHub via Portainer.

---

## 0. How to use this document

1. Want to change something? Go to **Section 9 (Impact Matrix)** and find your change type. It lists, in order, every file you must touch.
2. Want to know what a file is for? **Section 3 (Repo Tree)** annotates every file.
3. Want to know where data lives? **Section 4 (Database)** and **Section 5 (API Map)**.
4. Section 10 gives worked examples (the "add a text section" style of question).

The golden rule: **data flows DB → model → schema → service → api → nginx → frontend api.js → page.** Any change to stored data touches that whole chain, in that order. Changes that are display-only stop at the frontend.

---

## 1. Assumptions I made (please correct any that are wrong)

| # | Assumption | Why |
|---|---|---|
| A1 | "Always open Performance window, small, Indian time right top" = a **persistent top bar on every page** containing a mini performance strip (today P&L, open trades count, win rate of selected strategies) on the left/centre and a **live IST clock (Asia/Kolkata)** at the top right. | Requirement 4 is ambiguous. If you meant a floating widget, only `TopBar.jsx` changes. |
| A2 | Live prices come from **TwelveData** (`EUR/USD`, `GBP/USD`, `USD/JPY`; API key in `TWELVEDATA_API_KEY`; free plan is rate limited and delayed). yfinance was the original choice and was replaced, so the price layer is a **pluggable provider** (`price_providers/`) and a different source can be swapped in later. | Free forex feeds are all unofficial. Never hard-wire one. |
| A3 | Forex news calendar comes from a free weekly JSON/XML feed (Forex Factory mirror at `nfs.faireconomy.media`). It is unofficial and can change, so it is also behind a provider interface. **Verify the URL and format when building the news worker.** | Same reason as A2. |
| A4 | Prices are fetched **only for symbols that have an open trade**, by the worker, on a timer (default 30 s, setting-controlled), and cached in a `price_cache` table. The frontend never calls the internet; it only reads the cache from the backend. | Matches "only for open trades"; one fetch serves all users. |
| A5 | "Semi-automated" = the system detects things and **asks you to confirm**: SL/TP touched → alert "Close this trade?"; strategy rule violated → warning on save. It never closes or edits a trade on its own. | Safe for a journal. |
| A6 | Multi-user: every business row carries `user_id`. Roles: `admin`, `user`. Admin can view all data and manage accounts. | Requirement 3.4. |
| A7 | Migrations are applied by a **small runner at backend start-up** (tracks applied files in `schema_migrations`), not baked into the DB image. | Adding a migration then never requires wiping the Postgres volume. This avoids the "gotchas" class of problem in shadowDebt. |
| A8 | Deployment: Portainer → Stacks → *Repository* → `docker-compose.yml`, env vars entered in Portainer. Only nginx publishes a port, bound to your LAN. | "Local only". |
| A9 | P&L in phase 1 is shown in **pips/points, R-multiple and quote-currency**. Conversion to account currency (INR/USD) is a phase 2 item (needs FX conversion rates). | Keeps phase 1 correct and simple. |

---

## 2. Runtime architecture

```
 Browser (LAN)
     │  http://<host>:8080
     ▼
 ┌─────────┐   /api/*    ┌───────────┐    SQL     ┌───────────┐
 │  nginx  │────────────▶│  backend  │───────────▶│    db     │
 │ (proxy) │             │ (FastAPI) │            │ Postgres16│
 │         │  /*         └───────────┘            └───────────┘
 │         │────────┐          ▲                        ▲
 └─────────┘        ▼          │ (shared code/DB)       │
              ┌──────────┐  ┌──────────┐                │
              │ frontend │  │  worker  │────────────────┘
              │ (Vite    │  │ price +  │
              │  build)  │  │ news +   │──▶ Internet (TwelveData, news feed)
              └──────────┘  │ alerts   │
                            └──────────┘
 Volumes: pgdata · uploads (profile pics, trade screenshots) · backups
```

| Service | Role | Talks to |
|---|---|---|
| `db` | Postgres 16, all data | backend, worker |
| `backend` | REST API, auth, business logic, backup/restore, logging | db |
| `worker` | Only component that talks to the internet: price fetch (open trades), news fetch, SL/TP alert checks, scheduled backup | db, internet |
| `frontend` | React SPA (built static files) | via nginx → backend |
| `nginx` | Single entry point; `/api` → backend, everything else → frontend; upload size limit; (later) TLS | all |

Design choice: **backend and worker share the same Python code** (same image, different start command). This avoids duplicating models/services.

---

## 3. Repository tree (granular, annotated)

```
reapersJournal/
├── docker-compose.yml            # 5 services + volumes; Portainer entry point
├── .env.example                  # DB creds, JWT secret, price interval, TZ
├── .gitignore
├── README.md                     # Install via Portainer, quick start
├── LICENSE
├── docs/
│   ├── PLAN.md                   # this file
│   ├── CHANGELOG.md              # one line per change + which layers touched
│   └── runbook.md                # deploy / restore / troubleshoot
├── scripts/
│   └── backup.sh                 # host-side cron wrapper (calls /backup/run)
│
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf                # /api proxy, SPA fallback, client_max_body_size
│
├── db/
│   ├── Dockerfile                # plain postgres:16 (no baked schema)
│   └── migrations/
│       ├── 001_core_users.sql          # users, sessions/refresh, user_preferences
│       ├── 002_strategies.sql          # strategies, strategy_rules, strategy_deposits
│       ├── 003_instruments_markets.sql # markets, instruments (seeded with forex)
│       ├── 004_trades.sql              # trades, trade_condition_checks, trade_attachments
│       ├── 005_prices_news.sql         # price_cache, news_events
│       ├── 006_alerts_logs.sql         # alerts, app_logs (+ audit triggers)
│       ├── 007_settings.sql            # app_settings
│       └── seed_forex.sql              # majors/minors/gold + pip sizes
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py               # app factory, router registration, startup (run migrations)
│   │   ├── config.py             # env settings (pydantic-settings)
│   │   ├── database.py           # engine, SessionLocal, get_db
│   │   ├── migrate.py            # migration runner (schema_migrations)
│   │   ├── worker.py             # worker entry: schedules the jobs below
│   │   │
│   │   ├── api/                  # ROUTES — thin, validation + call service
│   │   │   ├── deps.py           # current_user, require_admin
│   │   │   ├── auth.py           # login, register(admin-gated), refresh
│   │   │   ├── users.py          # profile, password, avatar, admin user mgmt
│   │   │   ├── strategies.py     # CRUD strategies, rules, deposits
│   │   │   ├── instruments.py    # list markets/instruments for dropdowns
│   │   │   ├── trades.py         # journal CRUD, close trade, condition checks
│   │   │   ├── prices.py         # GET cached prices for open trades
│   │   │   ├── dashboard.py      # performance stats, mini-strip, default strategies
│   │   │   ├── news.py           # upcoming forex news
│   │   │   ├── alerts.py         # list / dismiss / confirm-close
│   │   │   ├── attachments.py    # screenshot + avatar upload/download
│   │   │   ├── backup.py         # run backup, download (own or all)
│   │   │   ├── restore.py        # restore (own or all, password required)
│   │   │   ├── logs.py           # master log viewer (admin=all, user=own)
│   │   │   ├── settings.py       # app + user preferences
│   │   │   └── help.py           # help articles (static/markdown driven)
│   │   │
│   │   ├── models/               # SQLAlchemy tables (1 file ≈ 1 table group)
│   │   │   ├── user.py
│   │   │   ├── preference.py
│   │   │   ├── strategy.py       # Strategy, StrategyRule, StrategyDeposit
│   │   │   ├── instrument.py     # Market, Instrument
│   │   │   ├── trade.py          # Trade, TradeConditionCheck
│   │   │   ├── attachment.py
│   │   │   ├── price.py          # PriceCache
│   │   │   ├── news.py           # NewsEvent
│   │   │   ├── alert.py
│   │   │   ├── app_log.py
│   │   │   └── setting.py
│   │   │
│   │   ├── schemas/              # Pydantic in/out shapes (mirror models)
│   │   │   ├── user.py  strategy.py  instrument.py  trade.py
│   │   │   ├── price.py  news.py  alert.py  dashboard.py
│   │   │   ├── log.py   setting.py  backup.py
│   │   │
│   │   ├── services/             # BUSINESS LOGIC — the only layer with rules
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── strategy_service.py     # rules/constraints/deposits logic
│   │   │   ├── trade_service.py        # open/close, rule-violation check, pnl calc
│   │   │   ├── pnl_service.py          # pips/points, R-multiple, unrealized/realized
│   │   │   ├── performance_service.py  # win rate, expectancy, drawdown, equity curve
│   │   │   ├── price_service.py        # read cache, staleness flag
│   │   │   ├── news_service.py
│   │   │   ├── alert_service.py        # SL/TP touch → alert
│   │   │   ├── backup_service.py       # dump + JSON export + attachments zip
│   │   │   ├── restore_service.py
│   │   │   ├── attachment_service.py
│   │   │   └── log_service.py          # THE master logger (see §8)
│   │   │
│   │   ├── providers/            # EXTERNAL DATA — swappable
│   │   │   ├── base.py                 # PriceProvider / NewsProvider interfaces
│   │   │   ├── price_twelvedata.py
│   │   │   └── news_ffcal.py
│   │   │
│   │   ├── jobs/                 # worker jobs, each calls services/providers
│   │   │   ├── fetch_prices.py         # open-trade symbols → provider → price_cache
│   │   │   ├── fetch_news.py
│   │   │   ├── check_alerts.py         # compare price_cache vs SL/TP
│   │   │   └── scheduled_backup.py
│   │   │
│   │   └── utils/
│   │       ├── security.py             # JWT, bcrypt
│   │       ├── trading_math.py         # pip size, lot→units, R calc
│   │       ├── table_registry.py       # ★ list of tables included in backup/restore
│   │       └── time.py                 # UTC store, IST display helpers
│   └── tests/
│
└── frontend/
    ├── Dockerfile
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx                     # routes
        ├── index.css                   # theme tokens (aqua-blue dark / light)
        ├── components/
        │   ├── Layout.jsx              # sidebar + TopBar + <Outlet/>
        │   ├── Sidebar.jsx             # nav items + profile pic + theme toggle (bottom)
        │   ├── TopBar.jsx              # mini performance strip + ClockIST
        │   ├── ClockIST.jsx            # Asia/Kolkata live clock
        │   ├── MiniPerformance.jsx
        │   ├── StrategyPicker.jsx      # multi-select (dashboard + journal)
        │   ├── MarketPicker.jsx        # Forex/Equity/Futures/Options/Crypto
        │   ├── ConditionChecklist.jsx  # strategy rules → tick boxes
        │   ├── NewsPanel.jsx
        │   ├── LivePriceBadge.jsx
        │   └── ProtectedRoute.jsx
        ├── pages/
        │   ├── Login.jsx
        │   ├── Dashboard.jsx
        │   ├── Strategies.jsx          # list
        │   ├── StrategyDetail.jsx      # edit rules, constraints, deposits
        │   ├── Journal.jsx             # trade list + filters
        │   ├── TradeForm.jsx           # add/edit trade
        │   ├── TradeDetail.jsx
        │   ├── Settings.jsx            # tabs: Profile / Accounts(admin) / Backup / Restore / Preferences
        │   ├── Help.jsx
        │   └── Logs.jsx
        ├── hooks/
        │   ├── useTheme.js
        │   ├── useAuth.js
        │   ├── useLivePrices.js        # polls /api/prices/open
        │   └── useDefaultStrategies.js
        └── utils/
            ├── api.js                  # axios instance + one function per endpoint
            ├── format.js               # numbers, pips, IST date formatting
            └── export.js
```

Layering rules (these make impact tracing predictable):
- `api/` never contains logic; it only validates and calls a service.
- `services/` never knows about HTTP.
- `providers/` are the only code that touches the internet.
- `jobs/` are the only code the worker schedules.
- Frontend pages never call axios directly; they call functions in `utils/api.js`.

---

## 4. Database design (Postgres 16)

Convention: every business table has `id`, `user_id` (FK users), `created_at`, `updated_at` (trigger-maintained). Times stored **UTC**, displayed IST.

### 4.1 Tables

| Table | Key columns | Notes |
|---|---|---|
| `users` | username, email, password_hash, role(`admin`/`user`), display_name, avatar_attachment_id, is_active | First registered user becomes admin. |
| `user_preferences` | user_id, theme(`dark`/`light`), default_strategy_ids int[], default_market, refresh_secs | Backs "default strategies" on dashboard. |
| `strategies` | user_id, name, description, market, funding_mode(`systematic`/`non_systematic`), sip_amount, sip_frequency, start_date, is_active | Systematic = recurring deposit plan. |
| `strategy_rules` | strategy_id, rule_type(`entry`/`exit`/`risk`/`filter`), label, params JSONB, is_required, sort_order | Constraints + the "conditions to check" in the journal. e.g. risk: `{max_risk_pct: 1}`, filter: `{sessions:["London"]}`. |
| `strategy_deposits` | strategy_id, amount, kind(`deposit`/`withdrawal`), date, note | Strategy balance = sum + realized P&L. |
| `markets` | code(`FOREX`,`IN_EQUITY`,`IN_FUTURES`,`IN_OPTIONS`,`CRYPTO`), name, is_enabled | Phase 1 enables only FOREX. |
| `instruments` | market_code, symbol, provider_symbol, pip_size, contract_size, quote_ccy, is_active | `EURUSD` / `EURUSD=X`. Equity/F&O later add `expiry`, `strike`, `option_type` via a new migration. |
| `trades` | user_id, strategy_id, instrument_id, direction(`long`/`short`), status(`open`/`closed`/`cancelled`), entry_price, size(lots), stop_loss, take_profit, opened_at, closed_at, exit_price, fees, pnl_realized, r_multiple, notes, tags text[], emotion, rule_violations JSONB | `rule_violations` snapshot is filled on save. |
| `trade_condition_checks` | trade_id, rule_id, passed bool, note | The ticked checklist for that trade. |
| `attachments` | user_id, owner_type(`trade`/`avatar`), owner_id, path, mime, size | Files on `uploads` volume. |
| `price_cache` | provider_symbol (PK), price, bid, ask, fetched_at, source | Written only by worker. |
| `news_events` | event_time_utc, currency, impact(`low`/`med`/`high`), title, forecast, previous, actual, source_uid (unique) | Written only by worker. |
| `alerts` | user_id, trade_id, kind(`sl_hit`/`tp_hit`/`rule_violation`/`system`), message, status(`new`/`seen`/`dismissed`/`actioned`) | |
| `app_logs` | ts, level, user_id, action, entity_type, entity_id, before JSONB, after JSONB, source(`api`/`worker`/`db_trigger`), error_text, request_id | The **master log**. |
| `app_settings` | key, value | Global (admin) settings. |
| `schema_migrations` | filename, applied_at | Migration runner. |

### 4.2 Relationships

```
users ─┬─< strategies ─┬─< strategy_rules
       │               └─< strategy_deposits
       ├─< trades >── strategies
       │     ├── instruments >── markets
       │     ├─< trade_condition_checks >── strategy_rules
       │     └─< attachments
       ├─< alerts >── trades
       ├── user_preferences
       └─< app_logs
price_cache  (keyed by instruments.provider_symbol, no FK on purpose)
news_events  (global, no user_id)
```

### 4.3 DB-level automation
- `updated_at` trigger on all business tables.
- Audit triggers on `trades`, `strategies`, `strategy_rules`, `strategy_deposits`, `users` write to `app_logs` with `source='db_trigger'`, so nothing can change data without leaving a trace (same dual-logging idea as shadowDebt).
- A view `v_trade_stats` (per user/strategy/day) feeds `performance_service`.

---

## 5. API map

All under `/api`. Auth = JWT. "Admin" = admin only; "Own" = own data (admin may pass `?user_id=`).

| Area | Endpoints | Router file → service |
|---|---|---|
| Auth | `POST /auth/login` · `POST /auth/refresh` · `POST /auth/register` (admin, or first user) | `auth.py` → `auth_service` |
| Users | `GET/PUT /users/me` · `PUT /users/me/password` · `POST /users/me/avatar` · Admin: `GET/POST/PUT/DELETE /users` | `users.py` → `user_service` |
| Strategies | `GET/POST /strategies` · `GET/PUT/DELETE /strategies/{id}` · `…/rules` · `…/deposits` | `strategies.py` → `strategy_service` |
| Instruments | `GET /markets` · `GET /instruments?market=` | `instruments.py` |
| Journal | `GET/POST /trades` · `GET/PUT/DELETE /trades/{id}` · `POST /trades/{id}/close` · `PUT /trades/{id}/checks` | `trades.py` → `trade_service`, `pnl_service` |
| Prices | `GET /prices/open` (cached prices + unrealized P&L for my open trades) | `prices.py` → `price_service`, `pnl_service` |
| Dashboard | `GET /dashboard/performance?strategy_ids=1,2&range=` · `GET /dashboard/mini` · `GET/PUT /dashboard/defaults` | `dashboard.py` → `performance_service` |
| News | `GET /news/upcoming?impact=&currency=` | `news.py` → `news_service` |
| Alerts | `GET /alerts` · `POST /alerts/{id}/dismiss` · `POST /alerts/{id}/confirm-close` | `alerts.py` → `alert_service`, `trade_service` |
| Attachments | `POST/GET/DELETE /attachments` | `attachments.py` |
| Backup | `POST /backup/run?scope=me\|all` · `GET /backup/download/{id}` · `GET /backup/list` | `backup.py` → `backup_service` |
| Restore | `POST /restore?scope=me\|all` (file + password) | `restore.py` → `restore_service` |
| Logs | `GET /logs?level=&user=&entity=&from=&to=` | `logs.py` → `log_service` |
| Settings | `GET/PUT /settings` (admin global) · `GET/PUT /settings/preferences` | `settings.py` |
| Help | `GET /help` · `GET /help/{slug}` | `help.py` |

---

## 6. Key data flows

### 6.1 Live prices (open trades only)
```
worker: jobs/fetch_prices.py  (every N seconds, skip FX weekend)
  1. SELECT DISTINCT provider_symbol FROM trades JOIN instruments WHERE status='open'
  2. providers/price_twelvedata.py → fetch
  3. UPSERT price_cache
  4. jobs/check_alerts.py → compare with SL/TP → INSERT alerts (+ app_logs)
frontend: hooks/useLivePrices.js → GET /api/prices/open every N s
  → LivePriceBadge on Journal + TradeDetail, MiniPerformance in TopBar
```
No open trades = zero outgoing internet calls. A `fetched_at` older than 3× interval is shown as **stale** in the UI.

### 6.2 Adding a journal entry
```
Journal → TradeForm.jsx
  pick Market → Instrument → Strategy (StrategyPicker)
  → ConditionChecklist.jsx loads strategy_rules
  → api.js createTrade() → POST /api/trades
  → trade_service: validate, compare with risk rules → store rule_violations → INSERT trades + checks
  → log_service.write('trade.create') → app_logs
  → (if violations) alert_service creates a rule_violation alert
```

### 6.3 Dashboard
`Dashboard.jsx` → `StrategyPicker` (initial value from `user_preferences.default_strategy_ids`) → `GET /dashboard/performance` → `performance_service` reads `v_trade_stats` → charts (equity curve, win rate, expectancy, max drawdown, P&L by pair/session). `NewsPanel` → `GET /news/upcoming`.

### 6.4 Backup / restore
- `backup_service` iterates `utils/table_registry.py`, exports JSON per table (filtered by `user_id` for scope=`me`), plus `pg_dump` for scope=`all`, plus attachments zip, into one timestamped folder/zip.
- Restore needs the user's password re-entered. Non-admin restore is limited to rows with their own `user_id` (ids are re-mapped on insert). Admin `scope=all` replaces everything.
- **The registry is the contract**: any new table must be added to `table_registry.py`, otherwise it silently is not backed up. (See Impact Matrix.)

---

## 7. Frontend structure and theme

- **Theme:** CSS variables in `index.css`. Dark (default): near-black navy background, aqua-blue accent (`#22d3ee` family). Light: white/slate with the same accent. `useTheme.js` toggles `data-theme` on `<html>` and saves to `user_preferences.theme`.
- **Layout:** `Layout.jsx` = `Sidebar` (left) + `TopBar` (top) + content. Sidebar bottom = avatar + theme switch. Nav order: Dashboard · Strategies · Journal · Settings · Help · Logs (Logs visible to all; admin sees everyone's).
- **Settings tabs:** Profile · Accounts (admin only) · Backup · Restore · Preferences.
- **Market-aware forms:** `MarketPicker` drives which fields `TradeForm` shows (config object per market in `utils/format.js` or a `marketFields.js`). Forex fields first; equity/F&O fields added later by extending that config + a migration.

---

## 8. Logging (master logger)

Everything goes through `services/log_service.py`:

| Source | What it records |
|---|---|
| `api` | Every POST/PUT/DELETE: who, action, entity, before/after JSON, request_id |
| `worker` | Job runs, provider failures, alert creation |
| `db_trigger` | Raw row changes on core tables (cannot be bypassed) |
| Errors | Unhandled exceptions via a FastAPI exception handler → `level=ERROR` with traceback text |

Implementation: a FastAPI middleware assigns `request_id`; services call `log_service.write(...)`; the global exception handler calls it on failure. `Logs.jsx` filters by level/user/entity/date; admin sees all users, others see only their own.

---

## 9. Change-Impact Matrix

Order shown is the order you should edit. "✱" = easy to forget.

| # | Change type | DB | models | schemas | services | api | nginx | frontend `utils/api.js` | frontend pages/components | worker/jobs | Also ✱ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **New field on an existing entity** (e.g. `trades.setup_screenshot_note`) | new migration `ALTER TABLE` | add column | add to in/out schema | pass through / validate | usually none | – | none (same endpoint) | form + detail/list | – | ✱ `table_registry` unchanged, but check backup JSON restore handles missing field in old backups; ✱ audit trigger auto-covers; ✱ Help text |
| 2 | **New table / entity** | new migration | new model | new schemas | new service | new router + register in `main.py` | – | new functions | new page/component, route in `App.jsx`, sidebar item | maybe | ✱ add to `table_registry.py`; ✱ add audit trigger; ✱ `log_service` calls; ✱ CHANGELOG |
| 3 | **New page / nav item only (display, no new data)** | – | – | – | maybe new aggregate in existing service | maybe new GET | – | maybe 1 function | page + `App.jsx` route + `Sidebar.jsx` | – | ✱ Help article |
| 4 | **New strategy rule type / constraint** | none if `params` JSONB (else migration) | `strategy.py` enum | rule schema | `strategy_service` (validate params) **and `trade_service` (enforce)** | – | – | – | `StrategyDetail.jsx` rule editor + `ConditionChecklist.jsx` | – | ✱ rule enforcement in `trade_service` is the part people forget |
| 5 | **New market** (e.g. Indian Options) | migration: seed `markets`, add columns (`expiry`,`strike`,`option_type`) | `instrument.py`, `trade.py` | schemas | `trade_service`, `pnl_service` (lot size / premium math) | – | – | – | `MarketPicker`, market field config, `TradeForm.jsx` | `price_<new>.py` provider + `fetch_prices.py` routing | ✱ `trading_math.py`; ✱ enable in `markets.is_enabled`; ✱ performance grouping |
| 6 | **New price/news provider or source change** | – | – | – | – | – | – | – | – | new file in `providers/`, select via setting | ✱ nothing else changes by design; ✱ `app_settings` key; ✱ stale-data UI |
| 7 | **New dashboard metric/chart** | maybe extend `v_trade_stats` view | – | `dashboard.py` schema | `performance_service` | `dashboard.py` | – | function if new endpoint | `Dashboard.jsx` widget | – | ✱ keep strategy multi-select filter applied |
| 8 | **Auth/role change** (e.g. new role) | migration (`role` values) | `user.py` | `user.py` | `auth_service`, `user_service` | `deps.py` guards | – | `api.js` | `ProtectedRoute`, Settings Accounts tab | – | ✱ backup/restore scope rules; ✱ logs visibility |
| 9 | **New setting** | `app_settings` row (no migration) or `user_preferences` column (migration) | `setting.py`/`preference.py` | `setting.py` | read where it is used | `settings.py` | – | – | Settings page | job reads it | ✱ default in `.env.example` if env-driven |
| 10 | **Change refresh interval / worker schedule** | – | – | – | – | – | – | `useLivePrices.js` interval | – | `worker.py` schedule | ✱ stale threshold = 3× interval |
| 11 | **Upload size / new file type** | – | – | – | `attachment_service` | `attachments.py` | `client_max_body_size` in `nginx.conf` | – | uploader component | – | ✱ backup zip includes it; ✱ volume size |
| 12 | **Change env var / port / volume** | – | – | – | – | – | maybe `nginx.conf` | – | – | – | `docker-compose.yml`, `.env.example`, Portainer stack env, README |
| 13 | **Theme/colour change only** | – | – | – | – | – | – | – | `index.css` tokens only | – | – |
| 14 | **Rename a column/table** (avoid; prefer additive) | migration (rename) | model | schema | all uses | – | – | – | all uses | jobs | ✱ `table_registry.py`; ✱ old backups no longer restore unless a mapping is added in `restore_service` |
| 15 | **Change P&L / R-multiple formula** | maybe backfill migration | – | – | `pnl_service`, `trading_math.py` | – | – | – | – | – | ✱ historical `pnl_realized`/`r_multiple` stored values need a recalculation endpoint or migration |

### 9.1 Layer → "what depends on me" quick reference

| If you change… | These will be affected |
|---|---|
| a **DB column/table** | model → schema → service → api → `api.js` → page; **backup (`table_registry`), restore, audit trigger, logs** |
| a **model** | schema, services using it, migration must match |
| a **schema** (Pydantic) | the API contract → `api.js` and every page that reads/sends that shape |
| a **service function** | every router and job that calls it; tests |
| an **api route (path/shape)** | `api.js` function, pages, nginx only if prefix changes |
| `nginx.conf` | all browser traffic; uploads; SPA routing |
| `api.js` | every page |
| `Layout.jsx` / `TopBar.jsx` | every page (top bar is global) |
| `index.css` tokens | every page |
| `price_cache` / provider | live prices, alerts, mini performance, unrealized P&L |
| `table_registry.py` | backup and restore completeness |
| `docker-compose.yml` | Portainer stack redeploy (all services) |

---

## 10. Worked examples

**E1 — "Add a Notes text section to trades"** (field on existing entity)
1. `db/migrations/008_trade_notes2.sql`: `ALTER TABLE trades ADD COLUMN post_trade_review TEXT;`
2. `models/trade.py`: add column.
3. `schemas/trade.py`: add optional field to Create/Update/Out.
4. `trade_service.py`: nothing, unless validation is needed.
5. `api/trades.py`: no change (schema carries it).
6. nginx: **no impact**.
7. `utils/api.js`: no change.
8. `TradeForm.jsx` + `TradeDetail.jsx`: add the textarea / display.
9. Auto-covered: audit trigger, backup (column-level), logs.
10. Add line to `docs/CHANGELOG.md`.

**E2 — "Add a Risk-Reward ≥ 2 constraint to strategies"**
`params` JSONB means no migration → `strategy_service` (accept `rr_min`) → `trade_service` (compute RR on save, populate `rule_violations`, raise alert) → `StrategyDetail.jsx` (rule editor option) → `ConditionChecklist.jsx` (show auto-evaluated tick).

**E3 — "Add Indian Options"** → row #5. The biggest piece is `pnl_service` (premium × lot size) and a new provider branch; everything else is additive.

**E4 — "Show news also inside the Journal page"** → row #3: only `Journal.jsx` embeds the existing `NewsPanel`; nothing in backend/db/nginx changes.

---

## 11. Deployment (Portainer)

1. Push repo to GitHub (branches: `main` = deploy, `dev` = work).
2. Portainer → Stacks → Add stack → **Repository** → URL, branch `main`, compose path `docker-compose.yml`.
3. Set env vars in Portainer: `POSTGRES_PASSWORD`, `JWT_SECRET`, `TZ=Asia/Kolkata`, `PRICE_REFRESH_SECS=30`, `PUBLIC_PORT=8080`.
4. Deploy. Backend runs migrations on start. First account created at the login page becomes admin.
5. Only `nginx` publishes a port. Bind it to your LAN IP (`192.168.x.x:8080:80`) so it is not reachable from outside.
6. Updates: push to `main` → Portainer "Pull and redeploy". Data persists in named volumes `pgdata`, `uploads`, `backups`.

---

## 12. Build roadmap

| Phase | Scope | Outcome |
|---|---|---|
| **0 — Skeleton** | compose, nginx, db, migration runner, backend health, frontend shell with theme, Sidebar, TopBar + IST clock | Deploys from Portainer, empty UI |
| **1 — Accounts & logs** | users, auth, roles, profile, avatar, `log_service`, Logs page | Multi-user + master log |
| **2 — Strategies** | strategies, rules/constraints, deposits | Strategy management |
| **3 — Journal (Forex)** | instruments seed, trades CRUD, checklist, close trade, attachments | Core journaling |
| **4 — Live prices** | worker, TwelveData provider, `price_cache`, unrealized P&L, SL/TP alerts | Semi-automation |
| **5 — Dashboard & news** | performance stats, multi-strategy filter, defaults, mini strip, news worker | Analytics |
| **6 — Backup/restore** | per-user + admin scopes, password-confirmed restore, scheduled backup | Data safety |
| **7 — Markets expansion** | Indian equity → futures → options → crypto (Impact row #5 each time) | Broader journal |
| **8 — Polish** | account-currency P&L, tags/emotion analytics, CSV/PDF export, Help content | Best personal tracker |

---

## 13. Risks and open decisions

1. **The price provider (TwelveData free plan) is rate limited and can be delayed**. Mitigated by the provider interface and stale-data indicators. Expect to swap or add a fallback later.
2. **News feed is unofficial** (A3). Same mitigation.
3. **Restore across users** needs id remapping and care. Build and test it in phase 6 with a dummy dataset before trusting it.
4. **Free-plan limits for Indian derivatives data**: yfinance coverage of NSE F&O is poor. Phase 7 may need a different source or manual price entry.
5. **P&L currency** (A9): decide your account currency before phase 8.

### Questions for you
- Confirm A1 (persistent top bar with mini performance + IST clock).
- Should a trade support **partial exits / scaling in** from day one? It adds a `trade_executions` table (migration + model + service change), cheaper to add now than later.
- Is a single "trading account" per user enough, or do you want multiple broker accounts per user (adds `trading_accounts` and an `account_id` on trades)?
