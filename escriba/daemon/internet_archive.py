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

import escriba.db as db
import escriba.dao as dao

logger = logging.getLogger(__name__)


async def run(*, interval: int):
    async with db.connect() as con:
        while True:
            for job in await dao.snapshot.listmany_ready_for_archivedotorg_update(
                con,
                100,
            ):
                if not (archived_url := job.stdout):
                    logger.warning(
                        "Job [ %s ] succeeded, but found no url on archive.org.",
                        job.uid,
                    )
                await dao.webpage.update_archivedotorg(
                    con, uid=job.uid, archived_url=archived_url
                )
                await con.commit()

            await asyncio.sleep(interval)
