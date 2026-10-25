import os
import logging
from sqlalchemy import text
from app.database import engine

MIGRATIONS_DIR = "/app/db/migrations"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    logger.info("Starting migration runner...")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

        result = conn.execute(text("SELECT filename FROM schema_migrations"))
        applied = {row[0] for row in result.fetchall()}
        logger.info(f"Previously applied migrations: {applied}")

        if not os.path.exists(MIGRATIONS_DIR):
            logger.error(f"Migrations directory not found at {MIGRATIONS_DIR}")
            return

        files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")])
        logger.info(f"Found SQL files: {files}")

        for file in files:
            if file not in applied:
                filepath = os.path.join(MIGRATIONS_DIR, file)
                with open(filepath, "r") as f:
                    # .strip() removes whitespace/newlines.
                    sql = f.read().strip()

                # --- NEW LOGIC: Skip empty files ---
                if not sql:
                    logger.info(f"Skipping {file} (file is empty)")
                    continue
                # -----------------------------------

                logger.info(f"Applying migration: {file}")
                try:
                    conn.execute(text(sql))
                    conn.execute(
                        text("INSERT INTO schema_migrations (filename) VALUES (:filename)"),
                        {"filename": file}
                    )
                    conn.commit()
                    logger.info(f"Successfully applied {file}")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to apply {file}: {e}")
                    raise e
