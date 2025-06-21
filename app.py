from flask import Flask
from flask_login import LoginManager
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import logging

from config import Config
from auth.routes import auth_bp
from items.routes import items_bp

from flask_wtf import CSRFProtect

# App factory
def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    csrf = CSRFProtect()
    csrf.init_app(app)

    # Logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize MongoDB (no explicit cert settings)
    client = MongoClient(
        app.config["MONGO_URI"],                # e.g. mongodb+srv://...
        serverSelectionTimeoutMS=app.config["MONGO_TIMEOUT_MS"],
        server_api=ServerApi("1")
    )
    try:
        client.server_info()
        logger.info("✅ Connected to MongoDB Atlas!")
    except Exception as e:
        logger.warning("⚠️ Initial MongoDB check failed: %s", e)
        raise

    # Attach DB to config
    app.db = client["items_db"]
    app.users_col = app.db["users"]
    app.items_col = app.db["items"]

    # Flask‐Login
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    from auth.models import User
    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return User.get_by_id(app.users_col, user_id)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)

    return app

# Create config for Gunicorn
app = create_app()
