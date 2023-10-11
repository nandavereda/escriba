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
import enum
import logging

logger = logging.getLogger(__name__)


class Strategy(enum.Enum):
    # informational extractors
    internet_archive = 1
    title = 2
    favicon = 3

    # simple extractors
    curl = 10
    wget = 11
    warc = 12

    # comprehensive extractors
    pdf = 20
    screenshot = 21
    dom = 22

    # post-processing capable extractors
    singlefile = 30
    readability = 31
    mercury = 32

    # specialized extractors
    git = 40
    ytdlp = 41

    @property
    def timeout(self) -> int:
        if self.value < 20:  # informational or simple strategies
            timeout = 90
        elif self.value < 40:  # browser mimicking strategies
            timeout = 180

        # specialized extractors
        elif self == self.git:
            timeout = 180
        elif self == self.ytdlp:
            timeout = 3600

        # undefined
        else:
            timeout = 60

        return timeout
