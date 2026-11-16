-- Least privilege for the API process (run once as the database owner, after the migrations).
-- The API connects as atlas_app: it can read and write rows but cannot change the schema,
-- cannot edit or delete ledger or audit rows, and cannot disable the triggers that guard them.
--   psql "$OWNER_DATABASE_URL" -v app_password="'choose-a-long-random-password'" -f server/roles.sql
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'atlas_app') THEN
        CREATE ROLE atlas_app LOGIN;
    END IF;
END $$;
ALTER ROLE atlas_app PASSWORD :app_password;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM atlas_app;
GRANT USAGE ON SCHEMA public TO atlas_app;
GRANT SELECT ON schema_version TO atlas_app;
GRANT SELECT, INSERT, UPDATE ON accounts, driver_profiles, kitchens, dishes, sessions, bank_accounts, payments, outbox TO atlas_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON login_failures TO atlas_app;
GRANT SELECT, INSERT ON payouts, ledger_entries, audit_log TO atlas_app;
