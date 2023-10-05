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
import enum
import logging
import sqlite3
import typing
import uuid

import escriba.dao as dao

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Snapshot:
    uid: uuid.UUID
    creation_time: datetime.datetime
    webpage_uid: uuid.UUID
    job_state: enum.Enum
    strategy_uid: enum.Enum
    modified_time: typing.Optional[datetime.datetime] = None
    result: str = None

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        return cls(**_fields_from_row(row))


async def create(
    connection, *, webpage_uid: uuid.UUID, strategy: enum.Enum, job_state: enum.Enum
) -> uuid.UUID:
    uid = uuid.uuid4()
    await _create(
        connection,
        uid=uid,
        job_state=job_state,
        strategy=strategy,
        webpage_uid=webpage_uid,
    )
    return uid


def _create(
    connection,
    *,
    uid: uuid.UUID,
    job_state: enum.Enum,
    strategy: enum.Enum,
    webpage_uid: uuid.UUID,
):
    return connection.execute(
        "INSERT INTO snapshot (uid, webpage_uid, strategy_uid, job_state_uid)"
        " VALUES (:uid, :webpage_uid, :strategy_uid, :job_state_uid);",
        dict(
            uid=uid.hex,
            webpage_uid=webpage_uid.hex,
            strategy_uid=strategy.value,
            job_state_uid=job_state.value,
        ),
    )


def _read_by_webpage(connection, *, webpage_uid: uuid.UUID):
    return connection.execute(
        "SELECT * from snapshot"
        " WHERE webpage_uid=:webpage_uid"
        " ORDER BY creation_time DESC",
        dict(webpage_uid=webpage_uid.hex),
    )


def _read_by_state(connection, *, job_state: enum.Enum):
    return connection.execute(
        "SELECT * from snapshot"
        " WHERE job_state_uid=:job_state_uid"
        " ORDER BY creation_time DESC",
        dict(job_state_uid=job_state.value),
    )


def _fields_from_row(row: sqlite3.Row):
    fields = dict(
        uid=uuid.UUID(row["uid"]),
        creation_time=datetime.datetime.fromisoformat(row["creation_time"]),
        job_state=dao.job.JobState(row["job_state_uid"]),
        strategy=dao.strategy.Strategy(row["strategy_uid"]),
        webpage_uid=uuid.UUID(row["webpage_uid"]),
    )
    if raw_modified_time := row["modified_time"]:
        fields["modified_time"] = datetime.datetime.fromisoformat(raw_modified_time)
    if raw_result := row["result"]:
        fields["result"] = raw_result
    return fields


def listmany_by_webpage(
    connection, size: int, *, webpage_uid: uuid.UUID
) -> typing.Tuple[Snapshot, ...]:
    cursor = _read_by_webpage(connection, webpage_uid=webpage_uid)
    return tuple(Snapshot.from_row(row) for row in cursor.fetchmany(size))


async def get_by_state(
    connection, *, job_state: enum.Enum
) -> typing.Optional[Snapshot]:
    cursor = await _read_by_state(connection, job_state=job_state)
    if row := await cursor.fetchone():
        return Snapshot.from_row(row)


def _update_state_by_uid(connection, *, uid: uuid.UUID, job_state: enum.Enum):
    return connection.execute(
        "UPDATE snapshot SET job_state_uid=:job_state_uid WHERE uid=:uid",
        dict(uid=uid.hex, job_state_uid=job_state.value),
    )


async def update(connection, *, uid: uuid.UUID, job_state: enum.Enum):
    await _update_state_by_uid(connection, uid=uid, job_state=job_state)
