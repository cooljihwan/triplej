"""DB 엔진·세션 생성."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

import config
from app.db.models import Base


def make_engine(url: str | None = None) -> Engine:
    url = url or config.DATABASE_URL
    engine = create_engine(url, future=True)
    if url.startswith("sqlite"):
        # SQLite 는 기본적으로 FK 를 강제하지 않으므로 켠다.
        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
