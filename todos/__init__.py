import os
from flask import Flask, abort
from flask_swagger_ui import get_swaggerui_blueprint
from todos.config import setup_logging, get_config
from todos.models.api.user_api import UserApi
from todos.models import db, migrate
from flask_login import LoginManager
from todos.views import api_spec, user_bp, login_bp, logout_bp, todolist_bp, task_bp

setup_logging()
login_manager = LoginManager()


class Todos:
    def __init__(self):
        # Create and configure app
        self.app = Flask(__name__)
        self.environment = os.getenv('FLASK_ENV', default='production')

        # load config
        self.load_config()

        # register blueprints
        self.app.register_blueprint(api_spec)
        self.app.register_blueprint(login_bp)
        self.app.register_blueprint(logout_bp)
        self.app.register_blueprint(user_bp)
        self.app.register_blueprint(todolist_bp)
        self.app.register_blueprint(task_bp)
        self.app.register_blueprint(get_swaggerui_blueprint('/api', '/api/v1/'), url_prefix='/api')

        # initialize database and migration tool
        db.init_app(self.app)
        migrate.init_app(self.app)

        # initialize login manager
        login_manager.init_app(self.app)
        login_manager.login_view = "login_bp"

    def load_config(self):
        # Append config read from config file
        self.app.config.from_object(get_config())

    @login_manager.user_loader
    def load_user(user_id):
        user_api = UserApi()
        return user_api.read_user_by_user_id(user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        abort(403)
