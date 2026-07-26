import logging
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy.exc import OperationalError


def wake_database(engine: Engine) -> None:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        logging.warning(
            "Database is inactive. Wait time is expected during cold starts."
        )


@lru_cache(maxsize=1)
def get_mysql_engine(
    user: str,
    password: str,
    host: str,
    port: int,
    database: str,
) -> Engine:
    url = URL.create(
        drivername="mysql+pymysql",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )

    engine = create_engine(url, pool_pre_ping=True)
    wake_database(engine)

    return engine
