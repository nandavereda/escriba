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
import time
import typing
import zmq
import zmq.asyncio

import escriba.messaging.MDP as MDP


class Worker(MDP.MajorDomoBase):
    """Majordomo Protocol Worker API

    Implements the MDP/Worker spec at http://rfc.zeromq.org/spec:7.
    """

    HEARTBEAT_LIVENESS = 3  # 3-5 is reasonable

    heartbeat_at = 0  # When to send HEARTBEAT (relative to time.time(), so in seconds)
    liveness = 0  # How many attempts left
    heartbeat = 2500  # Heartbeat delay, msecs
    reconnect = 2500  # Reconnect delay, msecs

    # Internal state
    expect_reply = False  # False only at start

    # Return address, if any
    reply_to = None

    def __init__(
        self,
        broker,
        service,
        logger: typing.Optional[logging.Logger] = None,
        timeout: float = 2.5,
    ):
        self.broker = broker
        self.service = service.encode()
        self.ctx = zmq.asyncio.Context()
        self.logger = logger if logger else logging.getLogger(__name__)
        self.timeout = timeout

    async def connect(self):
        await self._reconnect_to_broker()

    async def _reconnect_to_broker(self):
        """Connect or reconnect to broker"""
        if self.socket:
            self.socket.close()
        self.socket = self.ctx.socket(zmq.DEALER)
        self.socket.linger = 0
        self.socket.connect(self.broker)
        self.logger.debug("I: connecting to broker at %s...", self.broker)

        # Register service with broker
        await self._send_to_broker(MDP.W_READY, self.service, [])

        # If liveness hits zero, queue is considered disconnected
        self.liveness = self.HEARTBEAT_LIVENESS
        self.heartbeat_at = time.time() + 1e-3 * self.heartbeat

    async def _send_to_broker(self, command, option=None, msg=None):
        """Send message to broker.

        If no msg is provided, creates one internally
        """
        if msg is None:
            msg = []
        elif not isinstance(msg, list):
            msg = [msg]

        if option:
            msg = [option] + msg

        msg = [b"", MDP.W_WORKER, command] + msg
        self.logger.debug("I: sending %s to broker", command)
        self.dump(msg)
        await self.socket.send_multipart(msg)

    async def recv(
        self, reply: typing.Optional[typing.List[typing.Union[str, bytes]]]
    ) -> typing.Optional[typing.List[str]]:
        if reply is not None:
            if not isinstance(reply, list):
                reply = [reply]
            for idx, el in enumerate(reply):
                if isinstance(el, str):
                    b = el.encode()
                else:
                    b = el
                reply[idx] = b
        request = await self._recv(reply)
        if request:
            return [b.decode() for b in request]

    async def _recv(
        self, reply: typing.Optional[typing.List[bytes]] = None
    ) -> typing.Optional[typing.List[bytes]]:
        """Send reply, if any, to broker and wait for next request."""
        # Format and send the reply if we were provided one
        assert reply is not None or not self.expect_reply

        if reply is not None:
            assert self.reply_to is not None
            reply = [self.reply_to, b""] + reply
            await self._send_to_broker(MDP.W_REPLY, msg=reply)

        self.expect_reply = True

        while True:
            try:
                msg = await asyncio.wait_for(self.socket.recv_multipart(), self.timeout)
            except TimeoutError:
                self.liveness -= 1
                if self.liveness == 0:
                    self.logger.debug("W: disconnected from broker - retrying...")
                    await asyncio.sleep(1e-3 * self.reconnect)
                    await self._reconnect_to_broker()
            else:
                self.logger.debug("I: received message from broker: ")
                self.dump(msg)

                self.liveness = self.HEARTBEAT_LIVENESS
                # Don't try to handle errors, just assert noisily
                assert len(msg) >= 3

                empty = msg.pop(0)
                assert empty == b""

                header = msg.pop(0)
                assert header == MDP.W_WORKER

                command = msg.pop(0)
                if command == MDP.W_REQUEST:
                    # We should pop and save as many addresses as there are
                    # up to a null part, but for now, just save one...
                    self.reply_to = msg.pop(0)
                    # pop empty
                    empty = msg.pop(0)
                    assert empty == b""

                    service = msg.pop(0)

                    return msg  # We have a request to process
                elif command == MDP.W_HEARTBEAT:
                    # Do nothing for heartbeats
                    pass
                elif command == MDP.W_DISCONNECT:
                    await self._reconnect_to_broker()
                else:
                    self.logger.error("E: invalid input message: ")
                    self.dump(msg)

            # Send HEARTBEAT if it's time
            if time.time() > self.heartbeat_at:
                await self._send_to_broker(MDP.W_HEARTBEAT)
                self.heartbeat_at = time.time() + 1e-3 * self.heartbeat
