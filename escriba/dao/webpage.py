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
import urllib.parse
import uuid

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Webpage:
    uid: uuid.UUID
    url: urllib.parse.SplitResult
    creation_time: datetime.datetime
    transfer_job_uid: uuid.UUID
    transfer_uid: uuid.UUID
    title: typing.Optional[str] = None
    internet_archive: typing.Optional[urllib.parse.SplitResult] = None
    modified_time: typing.Optional[datetime.datetime] = None
    alt_title: str = dataclasses.field(init=False)

    def __post_init__(self):
        self.alt_title = "".join(
            (
                self.url.netloc,
                self.url.path,
                self.url.query,
            )
        )

    @property
    def safetitle(self) -> str:
        """Ensure a useful title for presenting in User Interface"""
        if self.title:
            return self.title
        return self.alt_title

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        return cls(**_fields_from_row(row))


async def create(
    connection, *, url: urllib.parse.SplitResult, transfer_job_uid: uuid.UUID
):
    url = urllib.parse.urlunsplit(url)
    cursor = await connection.execute(
        "SELECT uid FROM webpage WHERE url=:url", dict(url=url)
    )
    row = await cursor.fetchone()
    if row:
        uid = uuid.UUID(row["uid"])
    else:
        uid = uuid.uuid4()
        await connection.execute(
            "INSERT INTO webpage (uid, url) VALUES (:uid, :url)",
            dict(uid=uid.hex, url=url),
        )
    await connection.execute(
        "INSERT INTO webpage_transfer_job_association (webpage_uid, transfer_job_uid)"
        " VALUES (:webpage_uid, :transfer_job_uid)",
        dict(webpage_uid=uid.hex, transfer_job_uid=transfer_job_uid.hex),
    )
    return uid


def listmany_by_transfer(
    connection, size: int, *, transfer_uid: uuid.UUID
) -> typing.Tuple[Webpage, ...]:
    cursor = _read_by_transfer(connection, transfer_uid=transfer_uid)
    return tuple(Webpage.from_row(row) for row in cursor.fetchmany(size))


def _fields_from_row(row: sqlite3.Row):
    fields = dict(
        uid=uuid.UUID(row["uid"]),
        url=urllib.parse.urlsplit(row["url"]),
        creation_time=datetime.datetime.fromisoformat(row["creation_time"]),
        transfer_job_uid=uuid.UUID(row["transfer_job_uid"]),
        transfer_uid=uuid.UUID(row["transfer_uid"]),
    )
    if raw_modified_time := row["modified_time"]:
        fields["modified_time"] = datetime.datetime.fromisoformat(raw_modified_time)
    if raw_title := row["title"]:
        fields["title"] = raw_title
    if raw_internet_archive := row["internet_archive"]:
        fields["internet_archive"] = urllib.parse.urlsplit(raw_internet_archive)
    return fields


def _read_by_transfer(connection, *, transfer_uid: uuid.UUID):
    return connection.execute(
        "SELECT w.*, a.transfer_job_uid, j.transfer_uid from webpage as w"
        " JOIN webpage_transfer_job_association as a ON a.webpage_uid=w.uid"
        " JOIN transfer_job as j ON j.uid=a.transfer_job_uid"
        " WHERE j.transfer_uid=:transfer_uid"
        " ORDER BY w.creation_time DESC",
        dict(transfer_uid=transfer_uid.hex),
    )


def _read(connection, *, uid: uuid.UUID):
    return connection.execute(
        "SELECT w.*, a.transfer_job_uid, j.transfer_uid from webpage as w"
        " JOIN webpage_transfer_job_association as a ON a.webpage_uid=w.uid"
        " JOIN transfer_job as j ON j.uid=a.transfer_job_uid"
        " WHERE w.uid=:uid"
        " ORDER BY w.creation_time DESC",
        dict(uid=uid.hex),
    )


def get(connection, uid: uuid.UUID) -> Webpage:
    cursor = _read(connection, uid=uid)
    row = cursor.fetchone()
    return Webpage.from_row(row)


async def aget(connection, uid: uuid.UUID) -> Webpage:
    cursor = await _read(connection, uid=uid)
    row = await cursor.fetchone()
    return Webpage.from_row(row)


async def update_title(connection, uid: uuid.UUID, title: str):
    await connection.execute(
        "UPDATE webpage SET title=:title WHERE uid=:uid", dict(uid=uid.hex, title=title)
    )


async def update_archivedotorg(connection, uid: uuid.UUID, archived_url: str):
    await connection.execute(
        "UPDATE webpage SET archivedotorg=:archived_url WHERE uid=:uid",
        dict(uid=uid.hex, archived_url=archived_url),
    )
