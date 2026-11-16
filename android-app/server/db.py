"""PostgreSQL access for the ATLAS Go server: one connection per transaction, and numbered migrations.

psycopg 3 sends every value as a bound parameter (%s), never pasted into the SQL text, so user input
cannot change a statement's structure.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

MIGRATIONS = Path(__file__).with_name('migrations')
MIGRATION_LOCK = 4_150_000          # arbitrary application id for pg_advisory_xact_lock


class Database:
    def __init__(self, dsn: str):
        if not dsn or not dsn.startswith(('postgresql://', 'postgres://')):
            raise ValueError('DATABASE_URL must be a postgresql:// address.')
        self.dsn = dsn

    @contextmanager
    def transaction(self):
        """BEGIN ... COMMIT around the block; ROLLBACK if it raises. Statements and lock waits are
        bounded, so one stuck request cannot hold a connection for ever."""
        with psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=5,
                             options='-c statement_timeout=8000 -c lock_timeout=4000') as connection:
            yield connection

    def migrate(self) -> int:
        """Apply the numbered .sql files that have not run yet, each in its own transaction. A
        transaction-level advisory lock makes two servers starting together take turns."""
        with self.transaction() as db:
            if db.execute('SHOW server_encoding').fetchone()['server_encoding'] != 'UTF8':
                raise ValueError('The database must use UTF8 encoding (names and kitchens are Unicode text).')
            db.execute('SELECT pg_advisory_xact_lock(%s)', (MIGRATION_LOCK,))
            db.execute('CREATE TABLE IF NOT EXISTS schema_version '
                       '(version INTEGER PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())')
            current = db.execute('SELECT COALESCE(MAX(version), 0) AS v FROM schema_version').fetchone()['v']
        for path in sorted(MIGRATIONS.glob('[0-9][0-9][0-9]_*.sql')):
            version = int(path.name[:3])
            if version <= current:
                continue
            with self.transaction() as db:
                db.execute('SELECT pg_advisory_xact_lock(%s)', (MIGRATION_LOCK,))
                done = db.execute('SELECT 1 FROM schema_version WHERE version = %s', (version,)).fetchone()
                if not done:
                    db.execute(path.read_text(encoding='utf-8'))      # no parameters: a multi-statement script
                    db.execute('INSERT INTO schema_version (version) VALUES (%s)', (version,))
            current = version
        return current
