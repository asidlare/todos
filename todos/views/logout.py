import logging

from flask import Blueprint, jsonify
from flask.views import MethodView
from flask_login import logout_user, login_required
from todos.schemas.user import UserOK # noqa
from todos.models.api.user_api import UserApi

# logger
logger = logging.getLogger(__name__)

logout_bp = Blueprint('logout', __name__, url_prefix='/api/v1/logout')
user_api = UserApi()


class Logout(MethodView):

    @login_required
    def get(self):
        """
        ---
        tags:
        - "logout"
        summary: "Logout API"
        description: ""
        responses:
          200:
            description: "Successful operation"
            content:
                application/json:
                  schema: UserOK
        """
        logout_user()

        return jsonify({'response': "logout"}), 200

    @classmethod
    def register(cls):
        cls.collection_view = cls.as_view('logout')
        logout_bp.add_url_rule('', methods=['GET'], view_func=cls.collection_view, provide_automatic_options=True)


Logout.register()
