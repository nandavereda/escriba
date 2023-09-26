"""
    This file is part of Escriba.

    Copyright (C) 2022-2023 Fernanda Queiroz <dev@vereda.tec.br>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
"""
import importlib.resources
import logging
import sqlite3

import escriba.config as config
import escriba.db.connection as connection

logger = logging.getLogger(__name__)


def connect() -> connection.Connection:
    """Create and return a connection proxy to the sqlite database."""

    def connector() -> sqlite3.Connection:
        logger.debug("Creating a new sqlite3 connection.")
        conn = sqlite3.connect(
            config.DB_URI, timeout=1, detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.executescript(
            "PRAGMA journal_mode=WAL; PRAGMA synchronous = 1; BEGIN; PRAGMA busy_timeout = 30000; END;"
        )
        conn.row_factory = sqlite3.Row
        return conn

    return connection.Connection(connector, iter_chunk_size=64)


def recreate_database():
    """Clear the existing data and create new tables."""
    create_schema = importlib.resources.read_text(__package__, "schema.sql")
    logger.debug("About to execute recreate database script")
    with connect() as con:
        cursor = con.executescript(create_schema)
        con.commit()
        logger.debug("Recreate database operation returned %r", cursor.fetchone())


async def checkpoint():
    """Executes a wal checkpoint pragma."""
    logger.debug("Running sqlite3 checkpoint.")
    # Without this, in aproximately 2 hours, a 176K database generated a WAL of 4M in size.
    cursor = await connect().executescript("PRAGMA wal_checkpoint;")
    logger.debug("Checkpoint operation returned %r", cursor.fetchone())
