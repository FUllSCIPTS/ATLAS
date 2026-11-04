import json
import os
import sqlite3
import time
from contextlib import contextmanager
from uuid import uuid4

from packages.config import DATA, ROOT

DATABASE_URL = os.getenv("DATABASE_URL")
POSTGRES = bool(DATABASE_URL)


class DB:
    def __init__(self, connection):
        self.connection = connection

    def run(self, query, *args):
        return self.connection.execute(query.replace("?", "%s") if POSTGRES else query, args)


@contextmanager
def database():
    if POSTGRES:
        import psycopg
        from psycopg.rows import dict_row
        connection = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=5)
    else:
        DATA.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(DATA / "rides.sqlite", timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
    try:
        if not POSTGRES:
            connection.execute("BEGIN IMMEDIATE")
        yield DB(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def migrate():
    schema = (ROOT / "infra/schema.sql").read_text().replace(
        "__SEQUENCE__", "BIGSERIAL PRIMARY KEY" if POSTGRES else "INTEGER PRIMARY KEY"
    )
    with database() as db:
        for statement in schema.split(";"):
            if statement.strip():
                db.run(statement)
        for driver, distance, speed in (("driver-a", 1.5, 29), ("driver-b", 3.0, 23)):
            db.run("INSERT INTO drivers VALUES (?, 1, ?, ?, NULL) ON CONFLICT DO NOTHING", driver, distance, speed)


def emit(db, trip_id, event_type, **body):
    db.run("INSERT INTO outbox(event_id, trip_id, event_type, occurred_at, body) VALUES (?, ?, ?, ?, ?)",
           str(uuid4()), trip_id, event_type, int(time.time()), json.dumps(body))


def envelope(row):
    return {
        "schema_version": 1,
        "event_id": row["event_id"],
        "type": row["event_type"],
        "trip_id": row["trip_id"],
        "occurred_at": row["occurred_at"],
        "data": json.loads(row["body"]),
    }


if __name__ == "__main__":
    migrate()
