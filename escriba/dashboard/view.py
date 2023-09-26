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

import flask

import escriba.db as db
import escriba.dao.transfer as transfer

logger = logging.getLogger(__name__)

bp = flask.Blueprint("dashboard", __name__)


@bp.route("/", methods=["GET", "POST"])
def index_view():
    if flask.request.method == "POST":
        urls = flask.request.form["urls"]
        # TODO assert user input has lower and upper boundaries
        with db.connect() as con:
            _ = transfer.create_transfer(con, user_input=urls)
            con.commit()

        return flask.redirect(flask.url_for("dashboard.index_view"))

    with db.connect() as con:
        transfers = transfer.listmany(con, 10)

    return flask.render_template("index.html", transfers=transfers)
