"""Engine/session configuration. Dialect-specific setup stays in this module."""

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .db_models import Base

DEFAULT_DATABASE_URL = URL.create(
    "sqlite", database=str(Path(__file__).resolve().parents[1] / "chip_in.db")
).render_as_string(hide_password=False)


class Database:
    def __init__(self, url: str | None = None):
        self.url = make_url(
            url if url is not None else os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
        )
        options = {"pool_pre_ping": True}
        if self.url.get_backend_name() == "sqlite":
            options["connect_args"] = {"check_same_thread": False, "timeout": 30}
            if self.url.database in (None, "", ":memory:"):
                options["poolclass"] = StaticPool
        self.engine = create_engine(self.url, **options)
        if self.engine.dialect.name == "sqlite":

            @event.listens_for(self.engine, "connect")
            def configure_sqlite(connection, record):
                # Explicit transactions work consistently across supported Python versions.
                connection.isolation_level = None
                cursor = connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

            @event.listens_for(self.engine, "begin")
            def begin_sqlite(connection):
                connection.exec_driver_sql("BEGIN")

        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    def initialize(self):
        # Initial schema bootstrap only; existing tables/data are never dropped.
        Base.metadata.create_all(self.engine)

    def close(self):
        self.engine.dispose()
