from sqlalchemy import text


def set_price(db, provider_symbol, price, age_seconds=0):
    """Seed/refresh a price_cache row. age_seconds > 0 makes it stale."""
    db.execute(text("""
        INSERT INTO price_cache (provider_symbol, price, source, fetched_at)
        VALUES (:s, :p, 'test', now() - make_interval(secs => :age))
        ON CONFLICT (provider_symbol) DO UPDATE
        SET price = EXCLUDED.price, fetched_at = EXCLUDED.fetched_at
    """), {"s": provider_symbol, "p": price, "age": age_seconds})
    db.commit()
