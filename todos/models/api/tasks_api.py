from uuid import uuid4
from datetime import datetime
import logging
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from todos.models.definitions import (db, TodoListTbl, UserTbl, TaskTbl, TaskStatusChangeLogTbl)
from tools import timer


logger = logging.getLogger('todos')


class TaskApi():

    def __init__(self, user_id, todolist_id):
        self.user_id = user_id
        self.user = db.session.query(UserTbl).filter_by(user_id=self.user_id).first()
        self.todolist_id = todolist_id
        self.todolist = db.session.query(TodoListTbl).filter_by(todolist_id=self.todolist_id).first()

    def read_task_by_id(self, task_id):
        return db.session.query(TaskTbl).filter_by(task_id=task_id).filter_by(todolist_id=self.todolist_id).first()

    @timer
    def get_tasks(self, expand, task_id=None):
        if task_id:
            task = self.read_task_by_id(task_id)
            return list(task.descendants) if expand else list(task.children)
        else:
            tasks = list(self.todolist.children_tasks)
            if not tasks:
                return
            return list(tasks[0].dfs_tree) if expand else [row.to_dict() for row in self.todolist.children_tasks]

    def create_task(self, data):
        if data.get('parent_id', None):
            data['parent_id'] = str(data['parent_id'])

        try:
            task = TaskTbl(**data, todolist_id=self.todolist_id, task_id=str(uuid4()), created_ts=datetime.utcnow())
            db.session.add(task)
            db.session.add(TaskStatusChangeLogTbl(Task=task, changed_by=self.user_id, change_ts=task.created_ts,
                                                  status=data['status']))
            db.session.commit()
            return task
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return

    def update_task(self, task_id, data):
        task = self.read_task_by_id(task_id)
        if not task:
            return

        # task can have status done if all its descendants are done
        if data.get('status', None) and data['status'] == 'done':
            if not all(row['status'] == 'done' for row in task.descendants):
                return False

        try:
            db.session.query(TaskTbl).filter_by(task_id=task_id).update(data)
            if data.get('status', None):
                db.session.add(TaskStatusChangeLogTbl(task_id=task_id, changed_by=self.user_id,
                                                      change_ts=datetime.utcnow(), status=data['status']))
            db.session.commit()
            return True
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return

    def delete_task(self, task_id):
        task = self.read_task_by_id(task_id)
        if not task:
            return

        try:
            db.session.query(TaskTbl).filter_by(task_id=task_id).delete()
            db.session.commit()
            return True
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return

    @timer
    def purge_tasks(self):
        try:
            for task in db.session.query(TaskTbl).filter_by(status='done').all():
                if task.is_leaf or all(row['status'] == 'done' for row in task.dfs_tree_from_object(visited=list())):
                    db.session.query(TaskTbl).filter_by(task_id=task.task_id).delete()
            db.session.commit()
            return True
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return

    @timer
    def reparent_tasks(self, task_id, new_parent_id):
        task = self.read_task_by_id(task_id)
        if not task:
            return

        if not self._it_is_possible_to_reparent(task_id, new_parent_id):
            return False

        try:
            db.session.query(TaskTbl).filter_by(task_id=task_id).update({'parent_id': new_parent_id})
            db.session.commit()
            return True
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return

    def _it_is_possible_to_reparent(self, task_id, new_parent_id):
        # task cannot be the parent or None
        if task_id is None or task_id == new_parent_id:
            return False

        task = db.session.query(TaskTbl).filter_by(task_id=task_id).first()
        if task is None:
            return False

        if new_parent_id is None:
            empty_parent = True
            new_parent = None
        else:
            empty_parent = False
            new_parent = db.session.query(TaskTbl).filter_by(task_id=new_parent_id).first()
            # cannont be none after fetching from db
            if new_parent is None:
                return False

        # checking if new_parent_id
        # - it is not current parent of task
        if (empty_parent and task.parent_id is None) or (new_parent and task.parent_id == new_parent.task_id):
            return False

        # if still empty parent, no additional check is required
        if empty_parent:
            return True

        # - it is not one of task descendants
        if new_parent and any(row['task_id'] == new_parent.task_id for row in task.descendants):
            return False

        return True
