# Reaper's Journal - Operations Runbook

## 1. Deployment & Updates
- **Stack**: Docker Compose (Postgres 16, FastAPI backend, Vite React frontend, Nginx, Python Worker).
- **Environment**: Ensure `.env` is populated with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `JWT_SECRET`, `TWELVEDATA_API_KEY`, `PRICE_REFRESH_SECS`, and `TZ`.
- **Startup**: The backend container automatically runs `app.migrate.run_migrations()` on boot. Do not manually edit applied `.sql` files; create new ones for schema changes.

## 2. Admin & Account Management
- **First User**: The first account registered automatically receives the `admin` role. 
- **System Config UI**: Admins can toggle `maintenance_mode`, `allow_registration`, and adjust price refresh intervals dynamically via the **Settings > System** tab. These are hot-reloaded without needing a container restart.
- **User Deletion**: Admin deletion permanently wipes the user's trades, strategies, and physical image files from the volume. This action requires password confirmation.

## 3. Backup and Restore
- **Automated**: The worker generates a daily ZIP backup (JSON data + attachments) for the admin account to `/app/backups`.
- **Manual Export**: Users can download their own data via the Settings > Backup tab.
- **Restore Safety**: Uploading a backup ZIP **completely overwrites** the user's current data. The system safely maps old IDs to new Postgres IDs, recreating custom instruments if necessary. It strictly rejects mismatched strategy/trade IDs to prevent cross-account contamination.

## 4. Price & News Worker
- **Polling**: The worker polls TwelveData every `PRICE_REFRESH_SECS` (default 300s). It only fetches symbols for *currently open* trades to minimize API quota usage.
- **Timeouts**: If TwelveData times out or throws a 429, the worker logs it and retries safely on the next loop without crashing.

## 5. Testing and Development
- **Isolated Testing**: Running `pytest` automatically routes to an isolated SQLite database (`test_reapers.db`). It will not pollute your live Postgres database or your audit logs.
- **Dependencies**: `pytest` and `httpx` are intentionally omitted from the production Docker image. Install them locally in a virtual environment (`pip install -r requirements-dev.txt`) to run the suite.
