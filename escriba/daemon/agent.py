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

import escriba.config as config
import escriba.messaging as messaging

logger = logging.getLogger(__name__)


async def listener(program: str, **kwargs):
    sock = messaging.worker.Worker(**kwargs)
    await sock.connect()
    reply = None
    while True:
        logger.debug("Sending reply: %s", reply)
        request = await sock.recv(reply)
        logger.debug("Received request: %s", request)
        if request is None:
            break  # Worker was interrupted

        proc = await asyncio.create_subprocess_exec(
            program,
            *request,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()
        reply = [
            json.dumps(dict(rc=proc.returncode, help="Work finished.")),
            stdout,
            stderr,
        ]


async def run(*, endpoint: str, services: tuple = None):
    if not services:
        services = config.get_node_services()
    async with asyncio.TaskGroup() as tg:
        for name, concurrency, program in services:
            logger.info(
                "Creating [ %d ] listeners for program [ %s ]",
                concurrency,
                name,
            )
            for _ in range(concurrency):
                tg.create_task(listener(program, broker=endpoint, service=name))
