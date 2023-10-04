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
import asyncio
import logging
import typing
import urllib.parse

import escriba.db as db
import escriba.dao as dao

logger = logging.getLogger(__name__)


def _identify_transfer_urls(
    urls: str,
) -> typing.Generator[urllib.parse.SplitResult, None, None]:
    for urlline in urls.splitlines():
        urlline_stripped = urlline.strip()
        if not urlline_stripped:
            continue
        yield urllib.parse.urlsplit(urlline_stripped)


async def run(*, interval: int):
    async with db.connect() as con:
        while True:
            job = await dao.transfer_job.get_by_state(
                con, job_state=dao.job.JobState.PENDING
            )
            if job:
                await dao.transfer_job.update(
                    con,
                    uid=job.uid,
                    job_state=dao.job.JobState.EXECUTING,
                )
                await con.commit()
                transfer = await dao.transfer.aget(con, transfer_uid=job.transfer_uid)

                try:
                    for url in _identify_transfer_urls(transfer.user_input):
                        _ = await dao.webpage.create_webpage(
                            con, url=url, transfer_job_uid=job.uid
                        )
                    await con.commit()

                except Exception as exc:
                    await dao.transfer_job.update(
                        con,
                        uid=job.uid,
                        job_state=dao.job.JobState.FAILED,
                    )
                    await con.commit()
                    raise exc
                else:
                    await dao.transfer_job.update(
                        con,
                        uid=job.uid,
                        job_state=dao.job.JobState.SUCCEEDED,
                    )
                    await con.commit()
            await asyncio.sleep(interval)
