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

import escriba.db as db
import escriba.dao as dao

logger = logging.getLogger(__name__)


def _identity_archive_strategies(
    *_,
) -> typing.Generator[dao.strategy.Strategy, None, None]:
    # dummy. return all known strategies
    yield from dao.strategy.Strategy


async def run(*, interval: int):
    async with db.connect() as con:
        # Must clean the dirty state before starting the real loop.
        await dao.webpage_job.update_state(
            con, old_state=dao.job.JobState.EXECUTING, new_state=dao.job.JobState.FAILED
        )
        await con.commit()

        while True:
            if job := await dao.webpage_job.get_by_state(
                con, job_state=dao.job.JobState.PENDING
            ):
                await dao.webpage_job.update(
                    con,
                    uid=job.uid,
                    job_state=dao.job.JobState.EXECUTING,
                )
                await con.commit()

                webpage = await dao.webpage.aget(con, uid=job.webpage_uid)
                for strategy in _identity_archive_strategies(webpage.url):
                    _ = await dao.snapshot.create(
                        con,
                        webpage_uid=webpage.uid,
                        strategy=strategy,
                        job_state=dao.job.JobState.PENDING,
                    )
                await con.commit()

                await dao.webpage_job.update(
                    con,
                    uid=job.uid,
                    job_state=dao.job.JobState.SUCCEEDED,
                )
                await con.commit()
            await asyncio.sleep(interval)
