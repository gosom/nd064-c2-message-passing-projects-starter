import logging

from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api


def create_app(env=None):
    from app.config import config_by_name
    from app.routes import register_routes

    logging.basicConfig(level=logging.DEBUG)

    app = Flask(__name__)
    app.config.from_object(config_by_name[env or "test"])
    api = Api(app, title="UdaConnect API", version="0.1.0")

    CORS(app)  # Set CORS for development

    register_routes(api, app)

    @app.route("/health")
    def health():
        return jsonify("healthy")

    return app
