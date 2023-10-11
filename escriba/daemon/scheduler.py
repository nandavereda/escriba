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

import escriba.daemon as daemon
import escriba.messaging as messaging


async def run():
    async with asyncio.TaskGroup() as tg:
        # all these may become independent processes running under supervisord
        tg.create_task(daemon.agent.run(endpoint="tcp://localhost:5555"))
        tg.create_task(
            daemon.snapshot_job_worker.run(interval=1, endpoint="tcp://localhost:5555")
        )
        tg.create_task(daemon.transfer_job_worker.run(interval=3))
        tg.create_task(daemon.webpage_job_worker.run(interval=1))
        tg.create_task(messaging.broker.run("tcp://*:5555"))
