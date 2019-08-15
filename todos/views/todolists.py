import logging

from flask import Blueprint, request, jsonify
from flask.views import MethodView
from flask_login import current_user, login_required
from todos.schemas.todolists import TodoListPatch, TodoListPost, TodoListError, TodoListOK, TodoListGet # noqa
from todos.models.api.todolists_api import TodoListApi
from todos.models.api.user_api import UserApi

# logger
logger = logging.getLogger('todos')

todolist_bp = Blueprint('todolists', __name__, url_prefix='/api/v1/todolists')


class TodoList(MethodView):

    @login_required
    def get(self):
        """
        ---
        tags:
          - "todolist"
        summary: Returns one or all todolists per user
        parameters:
          - name: todolist_id
            in: query
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
          - name: label
            in: query
            schema:
              type: string
          - name: status
            in: query
            schema:
              type: string
              enum: [active, inactive]
          - name: priority
            in: query
            schema:
              type: string
              enum: [veryhigh, high, medium, low, verylow]
        responses:
          '200':
            description: "Successful operation"
            content:
              application/json:
                schema: TodoListGet
          '404':
            description: "No list available"
            content:
              application/json:
                schema: TodoListError
        """
        logged_user_id = current_user.user_id

        filters = dict()
        filters['label'] = request.args.get('label', default=None)
        filters['status'] = request.args.get('status', default=None)
        filters['priority'] = request.args.get('priority', default=None)

        # todolist
        todolist_id = request.args.get('todolist_id', default=None)

        todolist_api = TodoListApi(logged_user_id)
        data = tuple(todolist_api.get_todolists(todolist_id=todolist_id, filters=filters))
        logger.info(f"Getting {request.url} using {request.method}")

        if data:
            return jsonify(data), 200
        else:
            return jsonify({'error': 'No list available'}), 404

    @login_required
    def post(self):
        """
        ---
        tags:
          - "todolist"
        summary: Creates new todolists
        requestBody:
          required: true
          content:
            application/json:
              schema: TodoListPost
        responses:
          '201':
            description: "Successful operation"
            content:
              application/json:
                schema: TodoListGet
          '409':
            description: "Database error"
            content:
              application/json:
                schema: TodoListError
          '409':
            description: "Not correct input data"
            content:
              application/json:
                schema: TodoListError
        """
        logged_user_id = current_user.user_id

        schema, errors = TodoListPost().load(request.get_json())
        if errors:
            logger.error(f"Getting {request.url} using {request.method}, errors: {errors}")
            return jsonify({'error': errors}), 409

        logger.info(f"Getting {request.url} using {request.method} with schema {schema}")
        todolist_api = TodoListApi(logged_user_id)
        todolist = todolist_api.create_todolist(schema)

        if not todolist:
            logger.error(f"Getting {request.url} with {request.method}, database error")
            return jsonify({'error': 'Database error'}), 400

        return jsonify(todolist.to_dict()), 201

    @login_required # noqa
    def patch(self, todolist_id):
        """
        ---
        tags:
          - "todolist"
        summary: Changes todolists properties
        parameters:
          - name: todolist_id
            in: path
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
        requestBody:
          required: true
          content:
            application/json:
              schema: TodoListPatch
        responses:
          '200':
            description: "Successful operation"
            content:
              application/json:
                schema: TodoListOK
          '400':
            description: "Request with no data to change or database error"
            content:
              application/json:
                schema: TodoListError
          '403':
            description: "No permission for updating todolist"
            content:
              application/json:
                schema: TodoListError
          '404':
            description: "Not existing todolist"
            content:
              application/json:
                schema: TodoListError
          '409':
            description: "Bad format of input data"
            content:
              application/json:
                schema: TodoListError
        """
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no access to todolist {todolist_id}")
            return jsonify({'error': 'User with no access to todolist'}), 404

        if current_user.role(todolist_id) == 'reader':
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"has got no permission to update todolist {todolist_id}")
            return jsonify({'error': 'No permission for updating todolist'}), 403

        schema, errors = TodoListPatch().load(request.get_json())
        if errors:
            logger.error(f"Getting {request.url} using {request.method}, errors {errors}")
            return jsonify({'error': errors}), 409

        if not schema:
            logger.debug(f"Getting {request.url} using {request.method}, no data to change")
            return jsonify({'error': 'Request with no data to change'}), 400

        todolist_api = TodoListApi(logged_user_id)
        todolist = todolist_api.read_todolist_by_id(todolist_id)

        to_change = dict()
        if schema.get('label', None) and schema['label'] != todolist.label:
            to_change['label'] = schema['label']

        # can be null
        if schema.get('description', None) != todolist.description:
            to_change['description'] = schema.get('description', None)

        if schema.get('status', None) and schema['status'] != todolist.status.name:
            to_change['status'] = schema['status']

        if schema.get('priority', None) and schema['priority'] != todolist.priority.value:
            to_change['priority'] = schema['priority']

        if to_change:
            logger.info(f"Getting {request.url} using {request.method} with schema {schema}")
            updated = todolist_api.update_todolist(todolist_id, to_change)
            if not updated:
                logger.error(f"Getting {request.url} with {request.method}, database error")
                return jsonify({'error': f"Database error"}), 400

        return jsonify({'response': f"TodoList {todolist.label} modified"}), 200

    @login_required
    def delete(self, todolist_id):
        """
        ---
        tags:
          - "todolist"
        summary: Deletes todolist
        parameters:
          - name: todolist_id
            in: path
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
        responses:
          '204':
            description: "Successful operation"
            content:
              application/json:
                schema: TodoListOK
          '400':
            description: "Database error"
            content:
              application/json:
                schema: TodoListError
          '401':
            description: "Not user logged in"
            content:
              application/json:
                schema: TodoListError
          '404':
            description: "Not existing user"
            content:
              application/json:
                schema: TodoListError
        """
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no access to todolist {todolist_id}")
            return jsonify({'error': 'User with no access to todolist'}), 404

        if current_user.role(todolist_id) != 'owner':
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"has got no permission to delete todolist {todolist_id}")
            return jsonify({'error': 'No permission for deleting todolist'}), 403

        todolist_api = TodoListApi(logged_user_id)
        todolist = todolist_api.read_todolist_by_id(todolist_id)

        deleted = todolist_api.delete_todolist(todolist_id)
        if not deleted:
            logger.error(f"Getting {request.url} with {request.method}, database error")
            return jsonify({'error': f"Database error"}), 400

        logger.info(f"Getting {request.url} using {request.method}")

        return jsonify({'response': f"TodoList {todolist.label} deleted"}), 200

    @login_required # noqa
    def put(self, todolist_id, email):
        """
        ---
        tags:
          - "todolist"
        summary: Manages permissions
        parameters:
          - name: todolist_id
            in: path
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
          - name: email
            in: path
            schema:
              type: string
              maxLength: 250
              minLength: 5
              pattern: ^[^@\s]+@[^@\s]+\.[^@\s]+$
              example: user@example.com
          - name: role
            in: query
            schema:
              type: string
              enum: [owner, admin, reader]
          - name: new_owner_role
            in: query
            schema:
              type: string
              enum: [admin, reader]
        responses:
          '200':
            description: "Successful operation"
            content:
              application/json:
                schema: TodoListOK
          '400':
            description: "Request with no data to change"
            content:
              application/json:
                schema: TodoListError
          '401':
            description: "No user logged in"
            content:
              application/json:
                schema: TodoListError
          '403':
            description: "No permission for updating todolist"
            content:
              application/json:
                schema: TodoListError
          '404':
            description: "Not existing todolist"
            content:
              application/json:
                schema: TodoListError
        """ # noqa
        if not current_user:
            return jsonify({'error': 'No user logged in'}), 401
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no access to todolist {todolist_id}")
            return jsonify({'error': 'User with no access to todolist'}), 404

        if current_user.role(todolist_id) != 'owner':
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"has got no permission to update todolist {todolist_id}")
            return jsonify({'error': 'No permission for updating todolist'}), 403

        if current_user.email == email:
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"has got no permission to his rights himself")
            return jsonify({'error': 'No permission for updating logged user rights itself'}), 403

        # check todolist
        todolist_api = TodoListApi(logged_user_id)
        todolist = todolist_api.read_todolist_by_id(todolist_id)

        # check user
        user_api = UserApi()
        user = user_api.read_user_by_email(email)
        if not user:
            logger.error(f"Getting {request.url} using {request.method}, not existing email {email}")
            return jsonify({'error': f"Not existing {email}"}), 404

        role_name = request.args.get('role', default=None)
        new_owner_role_name = None

        if role_name and role_name == 'owner':
            new_owner_role_name = request.args.get('new_owner_role', default=None)

        updated = todolist_api.permissions(todolist_id, user.user_id, role_name, new_owner_role_name)
        if not updated:
            logger.error(f"Getting {request.url} with {request.method}, database error")
            return jsonify({'error': f"Database error"}), 400

        logger.info(f"Getting {request.url} using {request.method}")

        return jsonify({'response': f"TodoList {todolist.label} updated"}), 200

    @classmethod
    def register(cls):
        cls.collection_view = cls.as_view('todolists')
        todolist_bp.add_url_rule('', view_func=cls.collection_view, methods=['GET', 'POST'],
                                 provide_automatic_options=True)
        cls.view = cls.as_view('todolist')
        todolist_bp.add_url_rule('/<todolist_id>', methods=['PATCH', 'DELETE'], view_func=cls.view,
                                 provide_automatic_options=True)
        cls.permission_view = cls.as_view('permissions')
        todolist_bp.add_url_rule('/permissions/<todolist_id>/<email>', methods=['PUT'], view_func=cls.permission_view,
                                 provide_automatic_options=True)


TodoList.register()
