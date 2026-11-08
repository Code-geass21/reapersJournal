-- FIX FOR BUG 36: Disable Phase 2 markets that were accidentally left enabled by an early version of migration 009.
-- The math layer currently assumes Forex pip sizes, so leaving these enabled risks corrupting portfolio P&L.

UPDATE markets
SET is_enabled = FALSE
WHERE code IN ('IN_EQUITY', 'IN_FUTURES', 'IN_OPTIONS', 'CRYPTO');
