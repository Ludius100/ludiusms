from flask import Flask

from config import HOMEPAGE_ORIGIN
from modules.registry import iter_enabled_modules, load_component
from routes.core import core_bp
from routes.media import media_bp


CORE_BLUEPRINTS = (
    core_bp,
    media_bp,
)


def cors(response):
    response.headers[
        "Access-Control-Allow-Origin"
    ] = HOMEPAGE_ORIGIN

    response.headers[
        "Access-Control-Allow-Methods"
    ] = "GET, POST, DELETE, OPTIONS"

    response.headers[
        "Access-Control-Allow-Headers"
    ] = "Content-Type, X-Upload-Offset"

    response.headers[
        "Cache-Control"
    ] = "no-store"

    return response


def _register_optional_modules(app, start_collectors):
    for _, module in iter_enabled_modules():
        blueprint = load_component(module["blueprint"])
        app.register_blueprint(blueprint)

        collector = module.get("collector")
        if start_collectors and collector:
            load_component(collector)()


def create_app(start_collectors=True):
    app = Flask(__name__)

    for blueprint in CORE_BLUEPRINTS:
        app.register_blueprint(blueprint)

    _register_optional_modules(
        app,
        start_collectors=start_collectors,
    )

    app.after_request(cors)

    return app


if __name__ == "__main__":
    create_app().run(
        host="0.0.0.0",
        port=8090
    )
