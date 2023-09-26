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


def create_transfer(connection, *, user_input: str) -> str:
    uid = uuid.uuid4().hex
    connection.execute(
        "INSERT INTO transfer (uid, user_input) VALUES (:uid, :user_input);",
        dict(uid=uid, user_input=user_input),
    )
    return uid


def _read_transfer(connection):
    return connection.execute("SELECT * from transfer ORDER BY creation_time DESC")


@dataclasses.dataclass
class Transfer:
    uid: str
    creation_time: datetime.datetime
    user_input: str


def _transfer_from_row(row: sqlite3.Row):
    fields = dict(
        uid=str(uuid.UUID(row["uid"])),
        creation_time=datetime.datetime.fromisoformat(row["creation_time"]),
        user_input=row["user_input"],
    )
    return Transfer(**fields)


def listmany(connection, size: int) -> typing.Tuple[Transfer, ...]:
    return tuple(
        _transfer_from_row(row) for row in _read_transfer(connection).fetchmany(size)
    )
