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
import contextlib
import logging
import sys
import urllib.error
import urllib.request


def configure_logger(log: logging.Logger, level: str = "INFO") -> None:
    if log.hasHandlers():
        log.warning("Current handlers will not be altered.")
    else:
        prefered_format = "%(levelname)s:%(name)s:%(lineno)s:%(message)s"
        formatter = logging.Formatter(prefered_format)
        # Tip: When a handler is created, the level is set to NOTSET
        # (which causes all messages to be processed).
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        log.addHandler(handler)

    # Tip: When a logger is created, the level is set to NOTSET
    # (which causes all messages to be processed when the logger
    # is the root logger, or delegation to the parent when the logger
    # is a non-root logger).
    # Note that the root logger is created with level WARNING.
    log.setLevel(level)


@contextlib.contextmanager
def openurl(url: str):
    """Avoid security warning

    Issue: [B310:blacklist] Audit url open for permitted schemes.
    Allowing use of file:/ or custom schemes is often unexpected.
    CWE: CWE-22 (https://cwe.mitre.org/data/definitions/22.html)

    More Info:
    https://bandit.readthedocs.io/en/1.7.4/blacklists/blacklist_calls.html
    """
    req = urllib.request.Request(url, method="GET")
    if req.type not in ("http", "https"):
        raise ValueError("Invalid URL scheme")
    with urllib.request.urlopen(req) as rep:  # nosec B310
        yield rep
