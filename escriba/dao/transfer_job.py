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
class TransferJob:
    uid: uuid.UUID
    creation_time: datetime.datetime
    transfer_uid: uuid.UUID
    job_state: enum.Enum
    modified_time: typing.Optional[datetime.datetime] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        return cls(**_fields_from_row(row))


def create(
    connection, *, transfer_uid: uuid.UUID, job_state_uid: enum.Enum
) -> uuid.UUID:
    uid = uuid.uuid4()
    connection.execute(
        "INSERT INTO transfer_job (uid, transfer_uid, job_state_uid)"
        " VALUES (:uid, :transfer_uid, :job_state_uid);",
        dict(
            uid=uid.hex,
            transfer_uid=transfer_uid.hex,
            job_state_uid=job_state_uid.value,
        ),
    )
    return uid


def _read_by_transfer(connection, *, transfer_uid: uuid.UUID):
    return connection.execute(
        "SELECT * from transfer_job"
        " WHERE transfer_uid=:transfer_uid"
        " ORDER BY creation_time DESC",
        dict(transfer_uid=transfer_uid.hex),
    )


def _read_by_state(connection, *, job_state: enum.Enum):
    return connection.execute(
        "SELECT * from transfer_job"
        " WHERE job_state_uid=:job_state_uid"
        " ORDER BY creation_time DESC",
        dict(job_state_uid=job_state.value),
    )


def _fields_from_row(row: sqlite3.Row):
    fields = dict(
        uid=uuid.UUID(row["uid"]),
        creation_time=datetime.datetime.fromisoformat(row["creation_time"]),
        job_state=dao.job.JobState(row["job_state_uid"]),
        transfer_uid=uuid.UUID(row["transfer_uid"]),
    )
    if raw_modified_time := row["modified_time"]:
        fields["modified_time"] = datetime.datetime.fromisoformat(raw_modified_time)
    return fields


def listmany_by_transfer(
    connection, size: int, *, transfer_uid: uuid.UUID
) -> typing.Tuple[TransferJob, ...]:
    cursor = _read_by_transfer(connection, transfer_uid=transfer_uid)
    return tuple(TransferJob.from_row(row) for row in cursor.fetchmany(size))


async def get_by_state(
    connection, *, job_state: enum.Enum
) -> typing.Optional[TransferJob]:
    cursor = await _read_by_state(connection, job_state=job_state)
    if row := await cursor.fetchone():
        return TransferJob.from_row(row)


def _update_state_by_uid(connection, *, uid: uuid.UUID, job_state: enum.Enum):
    return connection.execute(
        "UPDATE transfer_job SET job_state_uid=:job_state_uid WHERE uid=:uid",
        dict(uid=uid.hex, job_state_uid=job_state.value),
    )


async def update(connection, *, uid: uuid.UUID, job_state: enum.Enum):
    await _update_state_by_uid(connection, uid=uid, job_state=job_state)


async def update_state(connection, old_state: enum.Enum, new_state: enum.Enum):
    return await connection.execute(
        "UPDATE transfer_job SET job_state_uid=:old_uid WHERE job_state_uid=:new_uid",
        dict(old_uid=old_state.value, new_uid=new_state.value),
    )
