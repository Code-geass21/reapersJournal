# Changelog

## [1.1.0] - 2026-11-08
### Added
- **Initial Risk Tracking**: Added `initial_stop_loss` to trades for accurate R-Multiple tracking even after moving SL to breakeven.
- **Advanced Dashboard**: Added Max Drawdown, Net Funding, and Date Range filters to the Performance Dashboard.
- **Admin Settings API**: Added backend endpoints and UI hooks for `maintenance_mode` and `allow_registration` global toggles.
- **Log Retention**: Added 30-day automated pruning for `app_logs` to prevent database bloat.
- **Frontend Interceptors**: Added global Axios interceptors for handling 401 (Unauthorized) and 503 (Maintenance) responses.

### Fixed
- **Journal Integrity**: Consolidated trade closure logic. Implemented strict `Decimal` math for all lot sizing to eliminate ghost partials (e.g., 0.001 lots left open).
- **Rule Engine**: Fixed 500 error on rule creation. Added strict Pydantic validation forbidding unknown keys and `NaN`/`inf` parameters.
- **Live Prices**: Hardened TwelveData provider with timeouts, 429 Quota handling, and API key redaction. Fixed missing USD conversion crashes and requested canonical pairs for EUR/GBP/AUD/NZD.
- **Alerts**: Fixed looping alert bug where dismissed SL/TP alerts were immediately recreated.
- **Backup & Restore**: Secured payload by stripping `password_hash` and excluding system logs. Hardened restore process against unmapped foreign keys, path traversal, and orphaned files.
- **Security**: Restricted `admin` role assignment to the first registered user only. Enforced minimum password lengths and strict Email string validation. 
- **Worker Resilience**: Isolated background jobs with per-job `try/except` blocks to prevent single-job failures (like API timeouts) from crashing the entire worker loop.

## [1.1.1] - 2026-11-09
### Fixed (The Stabilization Batch)
- **Math & Precision**: Widened `exchange_rate` to `NUMERIC(20, 10)` to prevent P&L drift on micro-fractional pairs like JPY. Normalized incoming floats against stored Decimals to properly secure closed-trade modifications.
- **Resilience**: P&L calculations now fall back to the execution's historical exchange rate if the live provider times out, preventing 500 crashes during network outages.
- **Alert Logic**: Dismissed alerts no longer loop infinitely. Deduping now respects active message states, and alert generation uses nested transactions (`SAVEPOINT`) to prevent rolling back parent trades on failure.
- **Testing & Audit**: Tests now strictly isolate to a local `test_reapers.db` SQLite file. Database audit triggers now correctly capture the `user_id` across multi-commit requests via Python ContextVars.
- **Production Infrastructure**: Consolidated the frontend container. Nginx now natively builds and serves the optimized React static assets, eliminating the Node `serve` dependency.
