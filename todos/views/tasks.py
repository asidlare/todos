import logging
from flask import Blueprint, request, jsonify
from flask.views import MethodView
from flask_login import current_user, login_required
from todos.schemas.tasks import TaskPost, TaskGet, TaskPatch, TaskOK, TaskError # noqa
from todos.models.api.tasks_api import TaskApi

# logger
logger = logging.getLogger('todos')

task_bp = Blueprint('tasks', __name__, url_prefix='/api/v1/tasks')


class Task(MethodView):

    @login_required
    def get(self, todolist_id):
        """
        ---
        tags:
          - "task"
        summary: Returns task tree one level or expanded descendants
        parameters:
          - name: todolist_id
            in: path
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
          - name: expand
            in: query
            schema:
              type: boolean
          - name: task_id
            in: query
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
        responses:
          '200':
            description: "Successful operation"
            content:
              application/json:
                schema: TaskGet
          '404':
            description: "No task available or no access to todolist"
            content:
              application/json:
                schema: TaskError
        """
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            return jsonify({'error': 'User with no access to todolist'}), 404

        # additional query params
        expand = request.args.get('expand', default=None)
        task_id = request.args.get('task_id', default=None)

        task_api = TaskApi(logged_user_id, todolist_id)
        data = task_api.get_tasks(boolean(expand), task_id)
        logger.info(f"Getting {request.url} using {request.method}")

        if data:
            return jsonify(data), 200
        else:
            return jsonify({'error': 'No list available'}), 404

    @login_required
    def post(self, todolist_id):
        """
        ---
        tags:
          - "task"
        summary: Creates new tasks
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
              schema: TaskPost
        responses:
          '201':
            description: "Successful operation"
            content:
              application/json:
                schema: TaskGet
          '400':
            description: "Database error"
            content:
              application/json:
                schema: TaskError
          '403':
            description: "No permission to access todolist or create a task"
            content:
              application/json:
                schema: TaskError
          '409':
            description: "Not correct input data"
            content:
              application/json:
                schema: TaskError
        """
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no access to todolist {todolist_id}")
            return jsonify({'error': 'No permission to access todolist'}), 403

        if current_user.role(todolist_id) == 'reader':
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no permission to create task")
            return jsonify({'error': 'No permission to create task'}), 403

        schema, errors = TaskPost().load(request.get_json())
        if errors:
            logger.error(f"Getting {request.url} using {request.method}, errors: {errors}")
            return jsonify({'error': errors}), 409

        task_api = TaskApi(logged_user_id, todolist_id)
        task = task_api.create_task(schema)

        if not task:
            logger.error(f"Getting {request.url} with {request.method}, database error")
            return jsonify({'error': 'Database error'}), 400

        return jsonify(task.to_dict()), 201

    @login_required # noqa
    def patch(self, todolist_id, task_id):
        """
        ---
        tags:
          - "task"
        summary: Changes tasks properties
        parameters:
          - name: todolist_id
            in: path
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
          - name: task_id
            in: path
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
        requestBody:
          required: true
          content:
            application/json:
              schema: TaskPatch
        responses:
          '200':
            description: "Successful operation"
            content:
              application/json:
                schema: TaskOK
          '400':
            description: "Request with no data to change or database error"
            content:
              application/json:
                schema: TaskError
          '403':
            description: "No permission to access todolist or change a task"
            content:
              application/json:
                schema: TaskError
          '409':
            description: "Bad format of input data"
            content:
              application/json:
                schema: TaskError
        """
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no access to todolist {todolist_id}")
            return jsonify({'error': 'No permission to access todolist'}), 403

        if current_user.role(todolist_id) == 'reader':
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no permission to create task")
            return jsonify({'error': 'No permission to create task'}), 403

        schema, errors = TaskPatch().load(request.get_json())
        if errors:
            return jsonify({'error': errors}), 409

        if not schema:
            return jsonify({'error': 'Request with no data to change'}), 400

        task_api = TaskApi(logged_user_id, todolist_id)
        task = task_api.read_task_by_id(task_id)

        to_change = dict()
        if schema.get('label', None) and schema['label'] != task.label:
            to_change['label'] = schema['label']

        # can be null
        if schema.get('description', None) != task.description:
            to_change['description'] = schema.get('description', None)

        if schema.get('status', None) and schema['status'] != task.status.name:
            to_change['status'] = schema['status']

        if schema.get('priority', None) and schema['priority'] != task.priority.value:
            to_change['priority'] = schema['priority']

        if to_change:
            logger.info(f"Getting {request.url} using {request.method} with schema {schema}")
            updated = task_api.update_task(task_id, to_change)
            if updated is None:
                logger.error(f"Getting {request.url} with {request.method}, database error")
                return jsonify({'error': f"Database error"}), 400
            elif not updated:
                logger.error(f"Getting {request.url} using {request.method}, todolist {todolist_id}. "
                             f"No permission for updating task. Not all descendants are done.")
                return jsonify({'error': f"No permission for updating task. Not all descendants are done."}), 403

        return jsonify({'response': f"Task {task.label} modified"}), 200

    @login_required
    def delete(self, todolist_id):
        """
        ---
        tags:
          - "task"
        summary: Deletes task or purges done tasks
        parameters:
          - name: todolist_id
            in: path
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
          - name: action
            in: query
            schema:
              type: string
              enum: [delete, purge]
              required: true
          - name: task_id
            in: query
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
        responses:
          '204':
            description: "Successful operation"
            content:
              application/json:
                schema: TaskOK
          '400':
            description: "Database error"
            content:
              application/json:
                schema: TaskError
          '403':
            description: "No permission to access todolist or change a task"
            content:
              application/json:
                schema: TaskError
          '409':
            description: "task_id cannot be null"
            content:
              application/json:
                schema: TaskError
        """
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no access to todolist {todolist_id}")
            return jsonify({'error': 'No permission to access todolist'}), 403

        if current_user.role(todolist_id) == 'reader':
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no permission to create task")
            return jsonify({'error': 'No permission to create task'}), 403

        task_api = TaskApi(logged_user_id, todolist_id)

        action = request.args.get('action', default=None)
        task_id = request.args.get('task_id', default=None)
        logger.info(f"Getting {request.url} using {request.method}")

        if action == 'purge':
            deleted = task_api.purge_tasks()
        else:
            if not task_id:
                logger.error(f"Getting {request.url} using {request.method}: "
                             f"task_id cannot be null when action {action}")
                return jsonify({'error': f"task_id cannot be null"}), 409
            task = task_api.read_task_by_id(task_id)
            deleted = task_api.delete_task(task_id)

        if not deleted:
            logger.error(f"Getting {request.url} with {request.method}, database error")
            return jsonify({'error': f"Database error"}), 400

        if action == 'purge':
            return jsonify({'response': f"Tasks purged"}), 200
        else:
            return jsonify({'response': f"Task {task.label} deleted"}), 200

    @login_required # noqa
    def put(self, todolist_id, task_id):
        """
        ---
        tags:
          - "task"
        summary: Reparent task, moves it inside the todolist
        parameters:
          - name: todolist_id
            in: path
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
          - name: task_id
            in: path
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
          - name: new_parent_id
            in: query
            schema:
              type: string
              format: uuid
              example: 00000000-0000-0000-0000-000000000000
        responses:
          '200':
            description: "Successful operation"
            content:
              application/json:
                schema: TaskOK
          '400':
            description: "Request with no data to change"
            content:
              application/json:
                schema: TaskError
          '403':
            description: "No permission to access todolist or change a task"
            content:
              application/json:
                schema: TaskError
          '404':
            description: "Not existing todolist"
            content:
              application/json:
                schema: TaskError
        """
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no access to todolist {todolist_id}")
            return jsonify({'error': 'No permission to access todolist'}), 403

        if current_user.role(todolist_id) == 'reader':
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no permission to create task")
            return jsonify({'error': 'No permission to create task'}), 403

        logger.info(f"Getting {request.url} using {request.method}")
        new_parent_id = request.args.get('new_parent_id', default=None)

        # check task
        task_api = TaskApi(logged_user_id, todolist_id)
        task = task_api.read_task_by_id(task_id)

        updated = task_api.reparent_tasks(task_id, new_parent_id)

        if updated is None:
            logger.error(f"Getting {request.url} with {request.method}, database error")
            return jsonify({'error': f"Database error"}), 400
        elif not updated:
            logger.error(f"Getting {request.url} using {request.method}, user {current_user.login} "
                         f"with no permission to reparent task")
            return jsonify({'error': f"No permission to reparent task."}), 403

        return jsonify({'response': f"TodoList {task.label} updated"}), 200

    @classmethod
    def register(cls):
        cls.collection_view = cls.as_view('tasks')
        task_bp.add_url_rule('/<todolist_id>', view_func=cls.collection_view, methods=['GET', 'POST', 'DELETE'],
                             provide_automatic_options=True)
        cls.view = cls.as_view('task')
        task_bp.add_url_rule('/<todolist_id>/<task_id>', methods=['PATCH'], view_func=cls.view,
                             provide_automatic_options=True)
        cls.reparent_view = cls.as_view('reparent')
        task_bp.add_url_rule('/reparent/<todolist_id>/<task_id>', methods=['PUT'], view_func=cls.reparent_view,
                             provide_automatic_options=True)


Task.register()


def boolean(val):
    return True if val == 'true' else False if val == 'false' else None
