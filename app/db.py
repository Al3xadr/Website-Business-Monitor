import logging

from psycopg_pool import AsyncConnectionPool


logger = logging.getLogger(__name__)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    telegram_id     BIGINT NOT NULL UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sites (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url             TEXT NOT NULL,
    name            TEXT,
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sites_user_id ON sites (user_id);
CREATE INDEX IF NOT EXISTS idx_sites_enabled ON sites (enabled) WHERE enabled = TRUE;

CREATE TABLE IF NOT EXISTS checks (
    id              SERIAL PRIMARY KEY,
    site_id         INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    ok              BOOLEAN NOT NULL,
    status_code     INTEGER,
    response_time   REAL,
    reason          TEXT,
    checked_at      TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_checks_site_id_checked_at
    ON checks (site_id, checked_at DESC);
"""


class Database:
    """
    Асинхронный клиент PostgreSQL на пуле соединений.
    """

    def __init__(self, config):
        self.config = config
        self.pool = None

    # ─── Подключение / схема ────────────────────────────────────────

    async def connect(self):
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
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SCHEMA_SQL)
            await conn.commit()
        logger.info("Database schema is up to date")

    # ─── Users ───────────────────────────────────────────────────────

    async def get_or_create_user(self, telegram_id):
        """
        Возвращает id пользователя по telegram_id.
        Создаёт, если не существует.
        """
        if self.pool is None:
            return None

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id FROM users WHERE telegram_id = %s",
                    (telegram_id,),
                )
                row = await cur.fetchone()
                if row is not None:
                    return row[0]

                await cur.execute(
                    "INSERT INTO users (telegram_id) VALUES (%s) RETURNING id",
                    (telegram_id,),
                )
                row = await cur.fetchone()
            await conn.commit()

        logger.info("Created user telegram_id=%s id=%s", telegram_id, row[0])
        return row[0]

    async def get_user_by_telegram_id(self, telegram_id):
        if self.pool is None:
            return None

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, telegram_id, created_at FROM users WHERE telegram_id = %s",
                    (telegram_id,),
                )
                row = await cur.fetchone()

        if row is None:
            return None
        return {"id": row[0], "telegram_id": row[1], "created_at": row[2]}

    # ─── Sites ──────────────────────────────────────────────────────

    async def add_site(self, user_id, url, name=None):
        """Добавляет сайт. Возвращает site_id."""
        if self.pool is None:
            return None

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO sites (user_id, url, name) "
                    "VALUES (%s, %s, %s) RETURNING id",
                    (user_id, url, name),
                )
                row = await cur.fetchone()
            await conn.commit()

        logger.info("Added site id=%s url=%s for user_id=%s", row[0], url, user_id)
        return row[0]

    async def list_sites(self, user_id):
        """Список сайтов пользователя."""
        if self.pool is None:
            return []

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, url, name, enabled, created_at "
                    "FROM sites WHERE user_id = %s ORDER BY id",
                    (user_id,),
                )
                rows = await cur.fetchall()

        return [
            {
                "id": r[0],
                "url": r[1],
                "name": r[2],
                "enabled": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]

    async def get_site(self, site_id):
        """Возвращает сайт по id (любого пользователя)."""
        if self.pool is None:
            return None

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, user_id, url, name, enabled, created_at "
                    "FROM sites WHERE id = %s",
                    (site_id,),
                )
                row = await cur.fetchone()

        if row is None:
            return None
        return {
            "id": row[0],
            "user_id": row[1],
            "url": row[2],
            "name": row[3],
            "enabled": row[4],
            "created_at": row[5],
        }

    async def remove_site(self, site_id, user_id):
        """
        Удаляет сайт, только если он принадлежит user_id.
        Возвращает True, если удалено.
        """
        if self.pool is None:
            return False

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM sites WHERE id = %s AND user_id = %s RETURNING id",
                    (site_id, user_id),
                )
                row = await cur.fetchone()
            await conn.commit()

        if row is None:
            return False

        logger.info("Removed site id=%s for user_id=%s", site_id, user_id)
        return True

    async def get_enabled_sites(self):
        """
        Все включённые сайты всех пользователей.
        Для scheduler: он обходит их все.
        """
        if self.pool is None:
            return []

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT s.id, s.user_id, s.url, u.telegram_id "
                    "FROM sites s "
                    "JOIN users u ON u.id = s.user_id "
                    "WHERE s.enabled = TRUE "
                    "ORDER BY s.id",
                )
                rows = await cur.fetchall()

        return [
            {
                "id": r[0],
                "user_id": r[1],
                "url": r[2],
                "telegram_id": r[3],
            }
            for r in rows
        ]

    # ─── Checks ─────────────────────────────────────────────────────

    async def save_check(self, site_id, result):
        """Сохраняет результат проверки для конкретного сайта."""
        if self.pool is None:
            return False

        sql = """
            INSERT INTO checks (site_id, ok, status_code, response_time, reason, checked_at)
            VALUES (%(site_id)s, %(ok)s, %(status_code)s, %(response_time)s, %(reason)s, %(checked_at)s)
        """

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql, {
                        "site_id": site_id,
                        "ok": result["ok"],
                        "status_code": result["status_code"],
                        "response_time": result["response_time"],
                        "reason": result["reason"],
                        "checked_at": result["checked_at"],
                    })
                await conn.commit()
            return True
        except Exception as e:
            logger.error("Failed to save check to database: %s", e)
            return False

    # ─── Закрытие ───────────────────────────────────────────────────

    async def close(self):
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")