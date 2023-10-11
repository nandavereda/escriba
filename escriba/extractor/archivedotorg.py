#!/usr/bin/python3
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
import json
import logging
import sys
import typing

import util

_ARCHIVE_API = "http://archive.org/wayback/available"
IO_BYTES_COUNT = 1024 * 1024

logger = logging.getLogger(__name__)


def main(url: str) -> typing.Optional[str]:
    """
    https://archive.org/help/wayback_api.php

        : timestamp
    the timestamp to look up in Wayback. If not specified,
    the most recenty available capture in Wayback is returned.
    The format of the timestamp is 1-14 digits (YYYYMMDDhhmmss)

    ex:
        http://archive.org/wayback/available?url=example.com&timestamp=20060101
    """
    timestamp = "20110101"
    params = f"url={url}&timestamp={timestamp}" if timestamp else f"url={url}"

    with util.openurl(f"{_ARCHIVE_API}?{params}") as rep:
        page = rep.read(IO_BYTES_COUNT)

    logger.info("Received response from Archive API: %r", page)
    response = json.loads(page)

    if response["archived_snapshots"]:
        return response["archived_snapshots"]["closest"]["url"]


if __name__ == "__main__":
    util.configure_logger(logger)
    print(main(sys.argv[1]))
