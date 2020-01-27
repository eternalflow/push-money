from flask import Flask

from pushmoney.api import bp_api

app = Flask(__name__)


def app_init(flask_app):
    flask_app.register_blueprint(bp_api)

