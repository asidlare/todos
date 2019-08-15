import logging

from flask import Blueprint, request, jsonify
from flask.views import MethodView
from todos.schemas.user import UserGet, UserLogin, UserError # noqa
from flask_login import login_user
from todos.models.api.user_api import UserApi

# logger
logger = logging.getLogger(__name__)

login_bp = Blueprint('login', __name__, url_prefix='/api/v1/login')
user_api = UserApi()


class Login(MethodView):

    def post(self):
        """
        ---
        tags:
        - "login"
        summary: "Login API"
        description: ""
        requestBody:
            required: true
            content:
                application/json:
                    schema: UserLogin
        responses:
          200:
            description: "Successful operation"
            content:
                application/json:
                  schema: UserGet
          401:
            description: "login/password pair doesn't match"
            content:
                application/json:
                  schema: UserError
          409:
            description: "login or password not provided"
            content:
                application/json:
                  schema: UserError
        """
        schema, errors = UserLogin().load(request.get_json())
        if errors:
            logger.error(f"Getting {request.url} using {request.method}, errors: {errors}")
            return jsonify({'error': errors}), 409

        logger.info(f"Getting {request.url} using {request.method} user {schema['login']}")
        user = user_api.read_user_by_login(schema['login'])
        if user and user.is_authenticated(**schema):
            login_user(user, remember=True)
            return jsonify(user.to_dict()), 200

        logger.error(f"Getting {request.url} using {request.method}, {schema} doesn't match")
        return jsonify({'error': "login/password pair doesn\'t match"}), 401

    @classmethod
    def register(cls):
        cls.collection_view = cls.as_view('login')
        login_bp.add_url_rule('', methods=['POST'], view_func=cls.collection_view, provide_automatic_options=True)


Login.register()
