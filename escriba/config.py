"""
    This file is part of Escriba.

    Copyright (C) 2022 Fernanda Queiroz <vereda@mailbox.org>

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
import os
import sys
import typing


def configure_logger(log: typing.Optional[logging.Logger] = None) -> None:
    if not log:
        log = logging.getLogger(__package__)

    if log.hasHandlers():
        log.warning("Current handlers will not be altered.")
    else:
        prefered_format = "%(levelname)s:%(name)s:%(lineno)s:%(message)s"
        formatter = logging.Formatter(prefered_format)
        # Tip: When a handler is created, the level is set to NOTSET
        # (which causes all messages to be processed).
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        log.addHandler(handler)

    # Tip: When a logger is created, the level is set to NOTSET
    # (which causes all messages to be processed when the logger
    # is the root logger, or delegation to the parent when the logger
    # is a non-root logger).
    # Note that the root logger is created with level WARNING.
    log.setLevel(
        os.environ.get(
            "ESCRIBA_LOG_LEVEL", logging.getLevelName(log.getEffectiveLevel())
        )
    )


def get_node_services() -> typing.Generator[typing.Tuple[str, int, str], None, None]:
    if services := os.environ.get("ESCRIBA_SERVICES"):
        for name, concur, program in (s.split(":") for s in services.split(",")):
            yield name, int(concur), program


DB_URI = os.environ.get("ESCRIBA_DB_URI", ":memory:")
