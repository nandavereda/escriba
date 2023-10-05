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
import escriba.dao as dao

logger = logging.getLogger(__name__)

bp = flask.Blueprint("dashboard", __name__)


@bp.route("/", methods=["GET", "POST"])
def index_view():
    if flask.request.method == "POST":
        urls = flask.request.form["urls"]
        # TODO assert user input has lower and upper boundaries
        with db.connect() as con:
            transfer_uid = dao.transfer.create(con, user_input=urls)
            job_state_uid = dao.job.JobState.PENDING
            _ = dao.transfer_job.create(
                con,
                transfer_uid=transfer_uid,
                job_state_uid=job_state_uid,
            )
            con.commit()

        return flask.redirect(flask.url_for("dashboard.index_view"))

    with db.connect() as con:
        transfers = dao.transfer.listmany(con, 10)

    return flask.render_template("index.html", transfers=transfers)


@bp.route("/transfer/<uuid:transfer_uid>")
def transfer_view(transfer_uid):
    with db.connect() as con:
        transfer = dao.transfer.get(con, uid=transfer_uid)
        webpages = dao.webpage.listmany_by_transfer(con, 10, transfer_uid=transfer_uid)
    return flask.render_template("transfer.html", transfer=transfer, webpages=webpages)
