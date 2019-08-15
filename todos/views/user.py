import logging

from flask import Blueprint, request, jsonify
from flask.views import MethodView
from flask_login import current_user, login_required, logout_user
from todos.schemas.user import UserPost, UserPatch, UserGet, UserError, UserOK # noqa
from todos.models.api.user_api import UserApi

# logger
logger = logging.getLogger('todos')

user_bp = Blueprint('user', __name__, url_prefix='/api/v1/user')
user_api = UserApi()


class User(MethodView):

    @login_required
    def get(self):
        """
        ---
        tags:
          - "user"
        summary: Returns logged user
        responses:
          '200':
            description: "Successful operation"
            content:
              application/json:
                schema: UserGet
          '404':
            description: "Not existing user"
            content:
              application/json:
                schema: UserError
        """
        logged_user_id = current_user.user_id

        userdb = user_api.read_user_by_user_id(logged_user_id)
        logger.info(f"Getting {request.url} using {request.method} for login {userdb.login}")

        return jsonify(userdb.to_dict()), 200

    def post(self):
        """
        ---
        tags:
          - "user"
        summary: Creates a new user
        requestBody:
          required: true
          content:
            application/json:
              schema: UserPost
        responses:
          '201':
            description: "Successful operation"
            content:
              application/json:
                schema: UserGet
          '400':
            description: "Bad request - existing_user, email or database error"
            content:
              application/json:
                schema: UserError
          '409':
            description: "Not correct input data"
            content:
              application/json:
                schema: UserError
        """
        schema, errors = UserPost().load(request.get_json())
        if errors:
            logger.error(f"Getting {request.url} using {request.method}, errors: {errors}")
            return jsonify({'error': errors}), 409

        logger.info(f"Getting {request.url} using {request.method} user {schema['login']}")
        userdb = user_api.read_user_by_email(schema['email'])
        if userdb:
            logger.error(f"Getting {request.url} with {request.method}, email exists {schema['email']}")
            return jsonify({'error': 'Email exists'}), 400

        userdb = user_api.read_user_by_login(schema['login'])
        if userdb:
            logger.error(f"Getting {request.url} with {request.method}, login exists {schema['login']}")
            return jsonify({'error': 'Login exists'}), 400

        user_data = user_api.create_user(schema)

        if not user_data:
            logger.error(f"Getting {request.url} with {request.method}, database error")
            return jsonify({'error': 'Database error'}), 400

        return jsonify(user_data.to_dict()), 201

    @login_required # noqa
    def patch(self):
        """
        ---
        tags:
          - "user"
        summary: Can change user password, name, email for logged user
        requestBody:
          required: true
          content:
            application/json:
              schema: UserPatch
        responses:
          '200':
            description: "Successful operation"
            content:
              application/json:
                schema: UserGet
          '400':
            description: "Request with no data to change"
            content:
              application/json:
                schema: UserError
          '409':
            description: "Not correct input data"
            content:
              application/json:
                schema: UserError
        """
        logged_user_id = current_user.user_id

        schema, errors = UserPatch().load(request.get_json())
        if errors:
            logger.error(f"Getting {request.url} using {request.method}, errors {errors}")
            return jsonify({'error': errors}), 409

        if not schema:
            logger.debug(f"Getting {request.url} using {request.method}, no data to change")
            return jsonify({'error': 'Request with no data to change'}), 400

        userdb = user_api.read_user_by_user_id(logged_user_id)

        to_change = dict()

        if schema.get('password', None) and schema['password'] != userdb.password:
            to_change['password'] = schema['password']

        if schema.get('name', None) and schema['name'] != userdb.name:
            to_change['name'] = schema['name']

        if schema.get('email', None) and schema['email'] != userdb.email:
            exists = user_api.read_user_by_email(schema['email'])
            if exists:
                logger.error(f"Getting {request.url} with {request.method}, email exists {schema['email']}")
                return jsonify({'error': f"email {schema['email']} exists in database"}), 400
            to_change['email'] = schema['email']

        if to_change:
            logger.info(f"Getting {request.url} using {request.method} with schema {schema}")
            updated = user_api.update_user(logged_user_id, to_change)
            if not updated:
                logger.error(f"Getting {request.url} with {request.method}, database error")
                return jsonify({'error': f"Database error"}), 400

        return jsonify({'response': f"User {userdb.login} updated"}), 200

    @login_required
    def delete(self):
        """
        ---
        tags:
          - "user"
        summary: Deletes logged user
        responses:
          '200':
            description: "Successful operation"
            content:
              application/json:
                schema: UserOK
          '400':
            description: "Database error"
            content:
              application/json:
                schema: UserError
        """
        logged_user_id = current_user.user_id

        userdb = user_api.read_user_by_user_id(logged_user_id)
        logger.info(f"Getting {request.url} using {request.method}")

        deleted = user_api.delete_user(logged_user_id)
        if not deleted:
            logger.error(f"Getting {request.url} with {request.method}, database error")
            return jsonify({'error': f"Database error"}), 400

        logout_user()
        return jsonify({'response': f"User {userdb.login} deleted"}), 200

    @classmethod
    def register(cls):
        cls.collection_view = cls.as_view('user')
        user_bp.add_url_rule('', methods=['GET', 'POST', 'PATCH', 'DELETE'], view_func=cls.collection_view, provide_automatic_options=True)


User.register()
