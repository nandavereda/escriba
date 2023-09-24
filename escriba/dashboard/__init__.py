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
import datetime
import logging
import os

import flask

import escriba.dashboard.view as view

logger = logging.getLogger(__name__)


def create_app():
    app = flask.Flask(__name__)

    # Conceal where the template dynamic parts glue together.
    app.jinja_options.update(
        {
            "lstrip_blocks": True,
            "trim_blocks": True,
        }
    )

    # Let Flask config be overriden by environment variables with the same name
    app.config.from_mapping({k: v for k, v in os.environ.items() if k in app.config})

    # Deserialize environment variables into Python types used by Flask.
    # https://flask.palletsprojects.com/en/2.0.x/config/#configuring-from-environment-variables
    app.config.from_mapping(
        dict(
            PERMANENT_SESSION_LIFETIME=datetime.timedelta(
                seconds=int(os.environ.get("PERMANENT_SESSION_LIFETIME", "3600"))
            ),
            SESSION_PERMANENT=os.environ.get("SESSION_PERMANENT", "true").lower()
            in {"1", "true"},
        )
    )

    logger.debug("Flask app name: %s", app.name)

    # Show configuration items whenever we are debugging
    if logger.getEffectiveLevel() <= logging.DEBUG:
        for item in app.config.items():
            logger.debug("Flask app config '%s': '%s'", *item)

    app.register_blueprint(view.bp)

    return app
