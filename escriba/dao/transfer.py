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
import dataclasses
import datetime
import logging
import sqlite3
import typing
import uuid

logger = logging.getLogger(__name__)


def create(connection, *, user_input: str) -> uuid.UUID:
    uid = uuid.uuid4()
    connection.execute(
        "INSERT INTO transfer (uid, user_input) VALUES (:uid, :user_input);",
        dict(uid=uid.hex, user_input=user_input),
    )
    return uid


def _read(connection, *, uid: uuid.UUID = None):
    if uid:
        cursor = connection.execute(
            "SELECT * from transfer WHERE uid=:uid", dict(uid=uid.hex)
        )
    else:
        cursor = connection.execute(
            "SELECT * from transfer ORDER BY creation_time DESC"
        )
    return cursor


@dataclasses.dataclass
class Transfer:
    uid: uuid.UUID
    creation_time: datetime.datetime
    user_input: str

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        return cls(**_fields_from_row(row))


def _fields_from_row(row: sqlite3.Row):
    return dict(
        uid=uuid.UUID(row["uid"]),
        creation_time=datetime.datetime.fromisoformat(row["creation_time"]),
        user_input=row["user_input"],
    )


def listmany(connection, size: int) -> typing.Tuple[Transfer, ...]:
    cursor = _read(connection)
    return tuple(Transfer.from_row(row) for row in cursor.fetchmany(size))


def get(connection, uid: uuid.UUID) -> Transfer:
    cursor = _read(connection, uid=uid)
    row = cursor.fetchone()
    return Transfer.from_row(row)


async def aget(connection, uid: uuid.UUID) -> Transfer:
    cursor = await _read(connection, uid=uid)
    row = await cursor.fetchone()
    return Transfer.from_row(row)
