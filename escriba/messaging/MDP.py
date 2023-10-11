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
import binascii
import logging

import zmq.asyncio

#  This is the version of MDP/Client we implement
C_CLIENT = b"MDPC01"

#  This is the version of MDP/Worker we implement
W_WORKER = b"MDPW01"

#  MDP/Server commands, as strings
W_READY = b"\001"
W_REQUEST = b"\002"
W_REPLY = b"\003"
W_HEARTBEAT = b"\004"
W_DISCONNECT = b"\005"

commands = [None, b"READY", b"REQUEST", b"REPLY", b"HEARTBEAT", b"DISCONNECT"]


class MajorDomoBase:
    ctx: zmq.asyncio.Context
    socket: zmq.asyncio.Socket = None
    logger: logging.Logger

    def dump(self, msg):
        """Log each message frame neatly"""
        self.logger.debug("----------------------------------------")
        for part in msg:
            line = "[%03d] " % len(part)
            try:
                line += part.decode("ascii")
            except UnicodeDecodeError:
                line += r"0x%s" % binascii.hexlify(part).decode("ascii")
            self.logger.debug(line)
