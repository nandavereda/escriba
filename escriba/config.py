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
import os
import typing


def get_node_services() -> typing.Generator[typing.Tuple[str, int, str], None, None]:
    if services := os.environ.get("ESCRIBA_SERVICES"):
        for name, concur, program in (s.split(":") for s in services.split(",")):
            yield name, int(concur), program


DB_URI = os.environ.get("ESCRIBA_DB_URI", ":memory:")
