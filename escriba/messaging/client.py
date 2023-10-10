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
import logging
import typing

import zmq
import zmq.asyncio

import escriba.messaging.MDP as MDP


class Client(MDP.MajorDomoBase):
    """Majordomo Protocol Client API."""

    def __init__(
        self,
        broker,
        logger: typing.Optional[logging.Logger] = None,
        timeout: float = 2.5,
    ):
        self.broker = broker
        self.ctx = zmq.asyncio.Context()
        self.logger = logger if logger else logging.getLogger(__name__)
        self.timeout = timeout
        self._reconnect_to_broker()

    async def send(self, service: str, request: typing.Union[str, typing.List[str]]):
        if not isinstance(request, list):
            request = [request]
        await self._send(service.encode(), [s.encode() for s in request])

    async def recv(self) -> typing.Optional[typing.List[str]]:
        reply = await self._recv()
        if reply:
            return [b.decode() for b in reply]

    def _reconnect_to_broker(self):
        """Connect or reconnect to broker"""
        if self.socket:
            self.socket.close()
        self.socket = self.ctx.socket(zmq.DEALER)
        self.socket.linger = 0
        self.socket.connect(self.broker)
        self.logger.debug("I: connecting to broker at %s...", self.broker)

    async def _send(self, service: bytes, request: typing.List[bytes]):
        """Send request to broker"""
        # Prefix request with protocol frames
        # Frame 0: empty (REQ emulation)
        # Frame 1: "MDPCxy" (six bytes, MDP/Client x.y)
        # Frame 2: Service name (printable string)

        request = [b"", MDP.C_CLIENT, service] + request
        self.logger.debug("I: send request to '%s' service: ", service)
        self.dump(request)
        await self.socket.send_multipart(request)

    async def _recv(self) -> typing.Optional[typing.List[bytes]]:
        """Returns the reply message or None if there was no reply."""
        try:
            msg = await asyncio.wait_for(self.socket.recv_multipart(), self.timeout)
        except TimeoutError:
            self.logger.debug("W: permanent error, abandoning request")
        else:
            # if we got a reply, process it
            self.logger.debug("I: received reply:")
            self.dump(msg)

            # Don't try to handle errors, just assert noisily
            assert len(msg) >= 4

            empty = msg.pop(0)
            assert empty == b""
            header = msg.pop(0)
            assert MDP.C_CLIENT == header

            service = msg.pop(0)
            return msg
