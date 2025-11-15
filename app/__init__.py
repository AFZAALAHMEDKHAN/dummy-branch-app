from flask import Flask

from .config import Config

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config())

    # Lazy imports to avoid circular deps during app init
    from .routes.health import bp as health_bp
    from .routes.loans import bp as loans_bp
    from .routes.stats import bp as stats_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(loans_bp, url_prefix="/api")
    app.register_blueprint(stats_bp, url_prefix="/api")

    # CONCEPTUAL: Use the new variable (LOG_FORMAT) to configure the application's logging
    return app
