import os
from sqlalchemy import text
from app.database import engine

MIGRATIONS_DIR = "/app/db/migrations"

def run_migrations():
    with engine.connect() as conn:
        # 1. Ensure tracking table exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

        # 2. Get already applied migrations
        result = conn.execute(text("SELECT filename FROM schema_migrations"))
        applied = {row[0] for row in result.fetchall()}

        if not os.path.exists(MIGRATIONS_DIR):
            print(f"Migrations directory not found at {MIGRATIONS_DIR}")
            return

        # 3. Apply new migrations
        files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")])
        for file in files:
            if file not in applied:
                print(f"Applying migration: {file}")
                filepath = os.path.join(MIGRATIONS_DIR, file)
                with open(filepath, "r") as f:
                    sql = f.read()

                conn.execute(text(sql))
                conn.execute(
                    text("INSERT INTO schema_migrations (filename) VALUES (:filename)"),
                    {"filename": file}
                )
                conn.commit()
                print(f"Successfully applied {file}")
