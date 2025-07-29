import os
from collections.abc import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from typing import TypeAlias
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Request


load_dotenv()

DB_CONN_STRING: str = os.getenv("PREDICTIONS_DB_URL", "")
SessionMaker: TypeAlias = sessionmaker[Session]


def _create_engine(DB_CONN_STRING):
    engine = create_engine(DB_CONN_STRING)
    return engine


def create_session(engine: Engine):
    return sessionmaker(bind=engine, autocommit=False)


def get_db_session(request: Request):
    sessionmaker = request.app.state.sessionmaker
    session = sessionmaker()
    try:
        yield session
    except Exception as e:
        # add logs here
        session.rollback()
        raise
    finally:
        session.close()


