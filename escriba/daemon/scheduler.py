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

import escriba.config as config
import escriba.daemon as daemon
import escriba.messaging as messaging


async def run():
    config.configure_logger()
    async with asyncio.TaskGroup() as tg:
        # These tasks share no state in memory and communicate only by
        # database and/or network messages. All these may become
        # independent processes running under supervisord:
        tg.create_task(daemon.agent.run(endpoint="tcp://localhost:5555"))
        tg.create_task(daemon.internet_archive.run(interval=1))
        tg.create_task(
            daemon.snapshot_job.run(interval=1, endpoint="tcp://localhost:5555")
        )
        tg.create_task(daemon.title.run(interval=1))
        tg.create_task(daemon.transfer_job.run(interval=3))
        tg.create_task(daemon.webpage_job.run(interval=1))
        tg.create_task(messaging.broker.run("tcp://*:5555"))
