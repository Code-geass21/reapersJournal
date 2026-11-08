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
