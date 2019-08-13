import logging
from flask import Blueprint, request, jsonify
from flask.views import MethodView
from flask_login import current_user, login_required
from todos.schemas.tasks import (TaskPost, TaskGet, TaskPatch, TaskID, TaskExpand, TaskOK, TaskError, DelActionField,
                                 ParentID) # noqa
from todos.schemas.todolists import TodoListID # noqa
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
            schema: TodoListID
          - name: expand
            in: query
            schema: TaskExpand
          - name: task_id
            in: query
            schema: TaskID
        responses:
          '200':
            description: "Successful operation"
            content:
              application/json:
                schema: TaskGet
          '401':
            description: "No user logged in"
            content:
              application/json:
                schema: TaskError
          '404':
            description: "No task available or no access to todolist"
            content:
              application/json:
                schema: TaskError
        """
        if not current_user:
            return jsonify({'error': 'No user logged in'}), 401
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            return jsonify({'error': 'User with no access to todolist'}), 404

        # additional query params
        expand = request.args.get('expand', default=None)
        task_id = request.args.get('task_id', default=None)

        task_api = TaskApi(logged_user_id, todolist_id)
        data = task_api.get_tasks(boolean(expand), task_id)

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
            schema: TodoListID
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
          '401':
            description: "No user logged in"
            content:
              application/json:
                schema: TaskError
          '403':
            description: "No permission for creating task"
            content:
              application/json:
                schema: TaskError
          '404':
            description: "User with no access to todolist"
            content:
              application/json:
                schema: TaskError
          '500':
            description: "Not correct input data"
            content:
              application/json:
                schema: TaskError
        """
        if not current_user:
            return jsonify({'error': 'No user logged in'}), 401
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            return jsonify({'error': 'User with no access to todolist'}), 404

        if current_user.role(todolist_id) == 'reader':
            return jsonify({'error': 'No permission for creating task'}), 403

        schema, errors = TaskPost().load(request.get_json())
        if errors:
            return jsonify({'error': errors}), 500

        task_api = TaskApi(logged_user_id, todolist_id)
        task = task_api.create_task(schema)

        if not task:
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
            schema: TodoListID
          - name: task_id
            in: path
            schema: TaskID
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
            description: "Request with no data to change"
            content:
              application/json:
                schema: TaskError
          '401':
            description: "No user logged in"
            content:
              application/json:
                schema: TaskError
          '403':
            description: "No permission for updating task"
            content:
              application/json:
                schema: TaskError
          '404':
            description: "Not existing todolist / task"
            content:
              application/json:
                schema: TaskError
          '500':
            description: "Bad format of input data"
            content:
              application/json:
                schema: TaskError
        """
        if not current_user:
            return jsonify({'error': 'No user logged in'}), 401
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            return jsonify({'error': 'User with no access to todolist'}), 404

        if current_user.role(todolist_id) == 'reader':
            return jsonify({'error': 'No permission for updating task'}), 403

        schema, errors = TaskPatch().load(request.get_json())
        if errors:
            return jsonify({'error': errors}), 500

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
            updated = task_api.update_task(task_id, to_change)
            if updated is None:
                return jsonify({'error': f"Database error"}), 400
            elif not updated:
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
            schema: TodoListID
          - name: action
            in: query
            schema: DelActionField
          - name: task_id
            in: query
            schema: TaskID
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
          '401':
            description: "Not user logged in"
            content:
              application/json:
                schema: TaskError
          '404':
            description: "Not existing user"
            content:
              application/json:
                schema: TaskError
          '500':
            description: "task_id cannot be null"
            content:
              application/json:
                schema: TaskError
        """
        if not current_user:
            return jsonify({'error': 'No user logged in'}), 401
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            return jsonify({'error': 'User with no access to todolist'}), 404

        if current_user.role(todolist_id) == 'reader':
            return jsonify({'error': 'No permission for deleting todolist'}), 403

        task_api = TaskApi(logged_user_id, todolist_id)

        action = request.args.get('action', default=None)
        task_id = request.args.get('task_id', default=None)

        if action == 'purge':
            deleted = task_api.purge_tasks()
        else:
            if not task_id:
                return jsonify({'error': f"task_id cannot be null"}), 400
            task = task_api.read_task_by_id(task_id)
            deleted = task_api.delete_task(task_id)

        if not deleted:
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
            schema: TodoListID
          - name: task_id
            in: path
            schema: TaskID
          - name: new_parent_id
            in: query
            schema: ParentID
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
          '401':
            description: "No user logged in"
            content:
              application/json:
                schema: TaskError
          '403':
            description: "No permission for reparenting task"
            content:
              application/json:
                schema: TaskError
          '404':
            description: "Not existing todolist"
            content:
              application/json:
                schema: TaskError
        """
        if not current_user:
            return jsonify({'error': 'No user logged in'}), 401
        logged_user_id = current_user.user_id

        if not current_user.role(todolist_id):
            return jsonify({'error': 'User with no access to task'}), 404

        if current_user.role(todolist_id) == 'reader':
            return jsonify({'error': 'No permission for updating task'}), 403

        new_parent_id = request.args.get('new_parent_id', default=None)

        # check task
        task_api = TaskApi(logged_user_id, todolist_id)
        task = task_api.read_task_by_id(task_id)

        updated = task_api.reparent_tasks(task_id, new_parent_id)

        if updated is None:
            return jsonify({'error': f"Database error"}), 400
        elif not updated:
            return jsonify({'error': f"No permission for reparenting task."}), 403

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
