"""
    This file is part of Escriba.

    Copyright (C) 2023 Fernanda Queiroz <dev@vereda.tec.br>

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

    This file incorporates work covered by the following copyright and
    permission notice:

        Copyright (c) 2010-2013 iMatix Corporation and Contributors

        Permission is hereby granted, free of charge, to any person
        obtaining a copy of this software and associated documentation
        files (the "Software"), to deal in the Software without
        restriction, including without limitation the rights to use,
        copy, modify, merge, publish, distribute, sublicense, and/or
        sell copies of the Software, and to permit persons to whom the
        Software is furnished to do so, subject to the following
        conditions:

        The above copyright notice and this permission notice shall be
        included in all copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
        EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
        OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
        NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
        HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
        WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
        FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
        OTHER DEALINGS IN THE SOFTWARE.
"""
import asyncio
import binascii
import dataclasses
import logging
import time
import typing

import zmq
import zmq.asyncio

import escriba.messaging.MDP as MDP


@dataclasses.dataclass
class _Service:
    """a single Service"""

    name: str  # Service name
    requests: list = dataclasses.field(default_factory=list)  # List of client requests
    waiting: list = dataclasses.field(default_factory=list)  # List of waiting workers


@dataclasses.dataclass
class _Worker:
    """a Worker, idle or active"""

    identity: bytes  # hex Identity of worker
    address: bytes  # Address to route to
    expiry: float  # expires at this point, unless heartbeat
    service: typing.Optional[_Service] = None  # Owning service, if known


class Broker(MDP.MajorDomoBase):
    """Majordomo Protocol broker

    Implements the MDP spec at http://rfc.zeromq.org/spec:7.
    """

    # We'd normally pull these from config data
    INTERNAL_SERVICE_PREFIX = b"mmi."
    HEARTBEAT_LIVENESS = 3  # 3-5 is reasonable
    HEARTBEAT_INTERVAL = 2500  # msecs
    HEARTBEAT_EXPIRY = HEARTBEAT_INTERVAL * HEARTBEAT_LIVENESS

    def __init__(self, logger: typing.Optional[logging.Logger] = None):
        """Initialize broker state."""
        self.services = {}  # known services
        self.workers = {}  # known workers
        self.waiting = []  # idle workers
        self.heartbeat_at = (
            time.time() + 1e-3 * self.HEARTBEAT_INTERVAL
        )  # When to send HEARTBEAT
        self.ctx = zmq.asyncio.Context()
        self.logger = logger if logger else logging.getLogger(__name__)
        self.socket = self.ctx.socket(zmq.ROUTER)  # Socket for clients & workers
        self.socket.linger = 0

    def bind(self, endpoint):
        """Bind broker to endpoint, can call this multiple times.

        We use a single socket for both clients and workers.
        """
        self.socket.bind(endpoint)
        self.logger.debug("I: MDP broker/0.1.1 is active at %s", endpoint)

    async def mediate(self):
        """Main broker work happens here"""
        if msg := await asyncio.wait_for(
            self.socket.recv_multipart(), self.HEARTBEAT_INTERVAL
        ):
            self.logger.debug("I: received message:")
            self.dump(msg)

            sender = msg.pop(0)
            empty = msg.pop(0)
            assert empty == b""
            header = msg.pop(0)

            if MDP.C_CLIENT == header:
                await self._process_client(sender, msg)
            elif MDP.W_WORKER == header:
                await self._process_worker(sender, msg)
            else:
                self.logger.error("E: invalid message:")
                self.dump(msg)

        self._purge_workers()

        """Send heartbeats to idle workers if it's time"""
        if time.time() > self.heartbeat_at:
            for worker in self.waiting:
                """Send message to worker."""
                # Stack routing and protocol envelopes to start of message
                # and routing envelope
                msg = [worker.address, b"", MDP.W_WORKER, MDP.W_HEARTBEAT]

                self.logger.debug("I: sending %r to worker", MDP.W_HEARTBEAT)
                self.dump(msg)

                await self.socket.send_multipart(msg)

            self.heartbeat_at = time.time() + 1e-3 * self.HEARTBEAT_INTERVAL

    async def _process_client(self, sender, msg):
        """Process a request coming from a client."""
        assert len(msg) >= 2  # Service name + body
        service = msg.pop(0)
        # Set reply return address to client sender
        msg = [sender, b""] + msg
        if service.startswith(self.INTERNAL_SERVICE_PREFIX):
            """Handle internal service according to 8/MMI specification"""
            returncode = b"501"
            if b"mmi.service" == service:
                name = msg[-1]
                returncode = b"200" if name in self.services else b"404"
            msg[-1] = returncode

            # insert the protocol header and service name after the routing envelope ([client, ''])
            msg = msg[:2] + [MDP.C_CLIENT, service] + msg[2:]
            await self.socket.send_multipart(msg)
        else:
            await self._dispatch(self._require_service(service), msg)

    def _require_service(self, name):
        """Locates the service (creates if necessary)."""
        assert name is not None
        service = self.services.get(name)
        if service is None:
            service = _Service(name)
            self.services[name] = service

        return service

    async def _dispatch(self, service, msg):
        """Dispatch requests to waiting workers as possible"""
        assert service is not None
        if msg is not None:  # Queue message if any
            service.requests.append(msg)
        self._purge_workers()
        while service.waiting and service.requests:
            msg = service.requests.pop(0)
            worker = service.waiting.pop(0)
            self.waiting.remove(worker)
            """Send message to worker.

            If message is provided, sends that message.
            """
            if msg is None:
                msg = []
            elif not isinstance(msg, list):
                msg = [msg]

            # Stack routing and protocol envelopes to start of message
            # and routing envelope
            msg = [worker.address, b"", MDP.W_WORKER, MDP.W_REQUEST] + msg

            self.logger.debug("I: sending %r to worker", MDP.W_REQUEST)
            self.dump(msg)

            await self.socket.send_multipart(msg)

    def _purge_workers(self):
        """Look for & kill expired workers.

        Workers are oldest to most recent, so we stop at the first alive worker.
        """
        while self.waiting:
            w = self.waiting[0]
            if w.expiry >= time.time():
                break
            self.logger.debug("I: deleting expired worker: %s", w.identity)
            """Deletes worker from all data structures, and deletes worker."""
            assert w is not None
            if w.service is not None:
                w.service.waiting.remove(w)
            # for s in w.service:
            #    s.waiting.remove(w)
            self.workers.pop(w.identity)
            self.waiting.pop(0)

    async def _process_worker(self, sender, msg):
        """Process message sent to us by a worker."""
        assert len(msg) >= 1  # At least, command

        command = msg.pop(0)

        assert sender is not None
        identity = binascii.hexlify(sender)

        worker_ready = identity in self.workers

        """Finds the worker (creates if necessary)."""
        worker = self.workers.get(identity)
        if worker is None:
            worker = _Worker(
                identity, sender, time.time() + 1e-3 * self.HEARTBEAT_EXPIRY
            )
            self.workers[identity] = worker
            self.logger.debug("I: registering new worker: %s", identity)

        if MDP.W_READY == command:
            assert len(msg) >= 1  # At least, a service name
            service = msg.pop(0)
            # Not first command in session or Reserved service name
            if worker_ready or service.startswith(self.INTERNAL_SERVICE_PREFIX):
                self._delete_worker(worker, True)
            else:
                # Attach worker to service and mark as idle
                worker.service = self._require_service(service)
                await self._worker_waiting(worker)

        elif MDP.W_REPLY == command:
            if worker_ready:
                # Remove & save client return envelope and insert the
                # protocol header and service name, then rewrap envelope.
                client = msg.pop(0)
                empty = msg.pop(0)
                assert empty == b""
                msg = [client, b"", MDP.C_CLIENT, worker.service.name] + msg
                await self.socket.send_multipart(msg)
                await self._worker_waiting(worker)
            else:
                self._delete_worker(worker, True)

        elif MDP.W_HEARTBEAT == command:
            if worker_ready:
                worker.expiry = time.time() + 1e-3 * self.HEARTBEAT_EXPIRY
            else:
                self._delete_worker(worker, True)

        elif MDP.W_DISCONNECT == command:
            self._delete_worker(worker, False)
        else:
            self.logger.error("E: invalid message:")
            self.dump(msg)

    def _delete_worker(self, worker, disconnect):
        """Deletes worker from all data structures, and deletes worker."""
        assert worker is not None
        if disconnect:
            """Send message to worker."""
            # Stack routing and protocol envelopes to start of message
            # and routing envelope
            msg = [worker.address, b"", MDP.W_WORKER, MDP.W_DISCONNECT]

            self.logger.debug("I: sending %r to worker", MDP.W_DISCONNECT)
            self.dump(msg)

            self.socket.send_multipart(msg)

        if worker.service is not None:
            worker.service.waiting.remove(worker)
        self.workers.pop(worker.identity)

    async def _worker_waiting(self, worker):
        """This worker is now waiting for work."""
        # Queue to broker and service waiting lists
        self.waiting.append(worker)
        worker.service.waiting.append(worker)
        worker.expiry = time.time() + 1e-3 * self.HEARTBEAT_EXPIRY
        await self._dispatch(worker.service, None)


async def run(endpoint):
    broker = Broker()
    broker.bind(endpoint)
    while True:
        try:
            await broker.mediate()
        except KeyboardInterrupt:
            break  # Interrupted
