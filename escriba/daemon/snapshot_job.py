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
import json
import logging
import typing
import urllib.parse
import uuid

import escriba.db as db
import escriba.dao as dao
import escriba.messaging as messaging

logger = logging.getLogger(__name__)


async def _archive_file(
    endpoint: str,
    request: typing.List[str],
    snapshot: dao.snapshot.Snapshot,
    timeout: int,
) -> typing.Tuple[uuid.UUID, typing.Optional[typing.List[str]]]:
    client = messaging.client.Client(endpoint, timeout=timeout)

    await client.send(snapshot.strategy.name, request)

    reply = await client.recv()
    return snapshot.uid, reply


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

                task = asyncio.create_task(
                    _archive_file(
                        endpoint, [job.strategy.name, url], job, job.strategy.timeout
                    )
                )
                executing |= {task}

            if executing:
                logger.debug("Awaiting for completion.")
                done, executing = await asyncio.wait(
                    executing, timeout=interval, return_when="FIRST_EXCEPTION"
                )

                logger.debug("Collecting results.")
                # Collect results and ensure exceptions within the coroutine are raised
                for future in done:
                    uid, reply = await future
                    job_state = dao.job.JobState.FAILED
                    if reply:
                        raw_result, stdout, stderr = reply
                        result = json.loads(raw_result)
                        if result["rc"] == 0:
                            job_state = dao.job.JobState.SUCCEEDED
                        await dao.snapshot.update(
                            con,
                            uid=uid,
                            job_state=job_state,
                            result=raw_result,
                            stdout=stdout,
                            stderr=stderr,
                        )
                    else:
                        await dao.snapshot.update(
                            con,
                            uid=uid,
                            job_state=job_state,
                        )
                    await con.commit()
            else:
                await asyncio.sleep(interval)
