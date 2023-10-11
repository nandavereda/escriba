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
import escriba.messaging as messaging

logger = logging.getLogger(__name__)


async def _archive_file(
    endpoint: str,
    request: typing.List[str],
    snapshot: dao.snapshot.Snapshot,
    timeout: int,
):
    client = messaging.client.Client(endpoint, timeout=timeout)

    await client.send(snapshot.strategy.name, request)

    reply = await client.recv()
    if not reply:
        raise RuntimeError("No response received.")
    result = "\n".join(reply)
    return snapshot.uid, result


async def run(*, interval: int, endpoint: str):
    async with db.connect() as con:
        # Must clean the dirty state before starting the real loop.
        await dao.snapshot.update_state(
            con, old_state=dao.job.JobState.EXECUTING, new_state=dao.job.JobState.FAILED
        )
        await con.commit()

        executing = set()
        while True:
            if job := await dao.snapshot.get_by_state(
                con, job_state=dao.job.JobState.PENDING
            ):
                await dao.snapshot.update(
                    con, uid=job.uid, job_state=dao.job.JobState.EXECUTING
                )
                await con.commit()

                webpage = await dao.webpage.aget(con, uid=job.webpage_uid)
                url = urllib.parse.urlunsplit(webpage.url)
                logger.debug("Launching tasks.")
                # launch tasks
                # executing |= {asyncio.get_running_loop().create_task(
                task = asyncio.create_task(
                    _archive_file(endpoint, [job.strategy.name, url], job, 30)
                )
                executing |= {task}

            if executing:
                logger.debug("Awaiting for completion.")
                done, executing = await asyncio.wait(
                    executing, timeout=interval, return_when="FIRST_EXCEPTION"
                )

                logger.debug("Collecting results.")
                # Collect results and ensure exceptions within the coroutine are re-raised
                for future in done:
                    uid, result = await future
                    await dao.snapshot.update(
                        con,
                        uid=uid,
                        job_state=dao.job.JobState.SUCCEEDED,
                        result=result,
                    )
                    await con.commit()
            else:
                logger.debug("Awaiting for next iteration.")
                await asyncio.sleep(interval)
