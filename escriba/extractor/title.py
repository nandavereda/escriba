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
import logging
import sys
import typing
import urllib.error

import archivedotorg
import util

IO_BYTES_COUNT = 1024 * 1024

logger = logging.getLogger(__name__)


def main(url: str) -> typing.Optional[str]:
    if title := _obtain_title(url):
        return title

    logger.info("Could not obtain title directly.")

    if archived_url := archivedotorg.main(url):
        logger.info("Extracting title from archived url: %r", archived_url)
        return _obtain_title(archived_url)


def _obtain_title(url: str) -> typing.Optional[str]:
    try:
        with util.openurl(url) as rep:
            page = rep.read(IO_BYTES_COUNT)
    except urllib.error.HTTPError as exc:
        logger.info("Could not open url. %s", exc)
        return

    left, _, _ = page.partition(b"</title>")

    if not left:
        logger.info("Coult not find title tag.")
        return

    _, _, title = left.partition(b"<title>")

    title = title.decode()
    return title


if __name__ == "__main__":
    util.configure_logger(logger)
    print(main(sys.argv[1]))
