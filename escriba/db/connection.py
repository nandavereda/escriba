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
import logging
import sqlite3
import typing

import aiosqlite

logger = logging.getLogger(__name__)


class Connection(aiosqlite.Connection):
    async def close(self) -> None:
        """Complete queued queries/cursors and close the connection."""

        if self._connection is None:
            return

        # To achieve the best long-term query performance it is recommended
        # that applications run "PRAGMA optimize" (with no arguments) just
        # before closing each database connection. This pragma is usually
        # a no-op or nearly so and is very fast.
        #
        # Reference: https://www.sqlite.org/pragma.html#pragma_optimize
        try:
            logger.debug("Attempting to optimize the database.")
            await self._execute(self._conn.executescript, "PRAGMA optimize;")
        except Exception:
            logger.warning("Exception occurred while optimizing the database.")
            raise

        try:
            logger.debug("Closing a sqlite3 connection.")
            await self._execute(self._conn.close)
        except Exception:
            logger.warning("Exception occurred while closing connection.")
            raise
        finally:
            self._running = False
            self._connection = None

    def __enter__(self) -> typing.Self:
        """Connect to the actual sqlite database."""
        if self._connection is None:
            try:
                self._connection = self._connector()
            except Exception:
                self._connection = None
                raise

        return self._connection

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the connection."""

        if self._connection is None:
            return

        # To achieve the best long-term query performance it is recommended
        # that applications run "PRAGMA optimize" (with no arguments) just
        # before closing each database connection. This pragma is usually
        # a no-op or nearly so and is very fast.
        #
        # Reference: https://www.sqlite.org/pragma.html#pragma_optimize
        try:
            logger.debug("Attempting to optimize the database.")
            self._connection.executescript("PRAGMA optimize;")
        except Exception:
            logger.warning("Exception occurred while optimizing the database.")
            raise

        try:
            logger.debug("Closing a sqlite3 connection.")
            self._connection.close()
        except Exception:
            logger.warning("Exception occurred while closing connection.")
            raise
        finally:
            self._connection = None
