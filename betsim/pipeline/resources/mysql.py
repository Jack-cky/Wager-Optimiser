import pandas as pd
from dagster import ConfigurableResource
from sqlalchemy import delete, text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.engine import Engine

from betsim.shared.database import get_mysql_engine
from betsim.shared.schema import TABLES
from betsim.shared.settings import SentinelConfig


class MySQLResource(ConfigurableResource):
    user: str
    password: str
    host: str
    port: int
    database: str
    batch_size: int = 500

    def get_engine(self) -> Engine:
        return get_mysql_engine(
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )

    def read(self, table_name: str) -> pd.DataFrame:
        with self.get_engine().connect() as conn:
            return pd.read_sql_table(table_name, con=conn)

    def query(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        with self.get_engine().connect() as conn:
            return pd.read_sql(text(sql), con=conn, params=params)

    def upsert(
        self,
        df: pd.DataFrame,
        table_name: str,
        pkey: str = "gid",
    ) -> None:
        table = TABLES[table_name]

        with self.get_engine().begin() as conn:
            table.create(conn, checkfirst=True)

            # delete inference template
            conn.execute(
                delete(table).where(table.c.season == SentinelConfig.SEASON)
            )

            # upsert processed data
            records = df.where(pd.notna(df), None).to_dict(orient="records")
            columns = [column for column in df.columns if column != pkey]

            for start in range(0, len(records), self.batch_size):
                batch = records[start:start + self.batch_size]
                stmt = insert(table).values(batch)

                col_map = {column: stmt.inserted[column] for column in columns}
                conn.execute(stmt.on_duplicate_key_update(**col_map))
