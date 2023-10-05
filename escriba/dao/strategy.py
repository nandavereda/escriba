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
    title = 1
    favicon = 2
    wget = 3
    curl = 4
    warc = 5

    pdf = 10
    screenshot = 11
    dom = 12
    singlefile = 13
    readability = 14
    mercury = 15

    git = 20
    ytdlp = 21

    archivedotorg = 30
