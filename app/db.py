import logging

from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row


logger = logging.getLogger(__name__)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS checks (
    id              SERIAL PRIMARY KEY,
    url             TEXT NOT NULL,
    ok              BOOLEAN NOT NULL,
    status_code     INTEGER,
    response_time   REAL,
    reason          TEXT,
    checked_at      TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_checks_url_checked_at
    ON checks (url, checked_at DESC);
"""


class Database:
    """
    Асинхронный клиент PostgreSQL на пуле соединений.

    Пул создаётся при connect() и закрывается при close().
    Если подключение не удалось — self.pool остаётся None,
    и все методы работают в режиме "no-op" (ничего не делают).
    """

    def __init__(self, config):
        self.config = config
        self.pool = None

    async def connect(self):
        """Создаёт пул и инициализирует схему."""
        conninfo = (
            f"host={self.config['host']} "
            f"port={self.config['port']} "
            f"dbname={self.config['dbname']} "
            f"user={self.config['user']} "
            f"password={self.config['password']}"
        )

        try:
            self.pool = AsyncConnectionPool(
                conninfo=conninfo,
                min_size=1,
                max_size=5,
                open=False,
            )
            await self.pool.open()
            await self.pool.wait()

            logger.info(
                "Connected to PostgreSQL at %s:%s/%s",
                self.config["host"],
                self.config["port"],
                self.config["dbname"],
            )

            await self._init_schema()

        except Exception as e:
            logger.error("Failed to connect to PostgreSQL: %s", e)
            self.pool = None

    async def _init_schema(self):
        """Создаёт таблицы, если их нет."""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SCHEMA_SQL)
            await conn.commit()
        logger.info("Database schema is up to date")

    async def save_check(self, result):
        """
        Сохраняет результат проверки.
        Если пул не активен — тихо ничего не делает.
        """
        if self.pool is None:
            return False

        sql = """
            INSERT INTO checks (url, ok, status_code, response_time, reason, checked_at)
            VALUES (%(url)s, %(ok)s, %(status_code)s, %(response_time)s, %(reason)s, %(checked_at)s)
        """

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql, result)
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to save check to database: %s", e)
            return False

    async def close(self):
        """Закрывает пул."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")