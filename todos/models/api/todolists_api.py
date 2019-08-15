from uuid import uuid4
from datetime import datetime
import logging
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from todos.models.definitions import (db, TodoListTbl, UserTodoListTbl, TodoListCreatorTbl, TodoListStatusChangeLogTbl,
                                      UserTbl)
from tools import timer


logger = logging.getLogger('todos')


class TodoListApi():

    def __init__(self, user_id):
        self.user_id = user_id
        self.user = db.session.query(UserTbl).filter_by(user_id=self.user_id).first()

    def read_todolist_by_id(self, todolist_id):
        return db.session.query(TodoListTbl).filter_by(todolist_id=todolist_id).first()

    @timer
    def get_todolists(self, todolist_id=None, filters=None):
        if todolist_id:
            todo = db.session.query(TodoListTbl).filter_by(todolist_id=todolist_id).all()
            return (row.to_dict() for row in todo)
        else:
            return self.user.all_todolists(**filters)

    def create_todolist(self, data):
        try:
            todo = TodoListTbl(**data, todolist_id=str(uuid4()), created_ts=datetime.utcnow())
            db.session.add(todo)
            db.session.add(TodoListCreatorTbl(todolist_id=todo.todolist_id, created_by=self.user_id))
            db.session.add(UserTodoListTbl(todolist_id=todo.todolist_id, user_id=self.user_id, role='owner'))
            db.session.add(TodoListStatusChangeLogTbl(TodoList=todo, changed_by=self.user_id,
                                                      change_ts=todo.created_ts, status=data['status']))
            db.session.commit()
            return todo
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return

    def update_todolist(self, todolist_id, data):
        try:
            db.session.query(TodoListTbl).filter_by(todolist_id=todolist_id).update(data)
            if data.get('status', None):
                db.session.add(TodoListStatusChangeLogTbl(todolist_id=todolist_id, changed_by=self.user_id,
                                                          change_ts=datetime.utcnow(), status=data['status']))
            db.session.commit()
            return True
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return

    def delete_todolist(self, todolist_id):
        try:
            db.session.query(TodoListTbl).filter_by(todolist_id=todolist_id).delete()
            db.session.commit()
            return True
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return

    def permissions(self, todolist_id, user_id, role=None, new_owner_role=None):
        if self.user_id == user_id:
            return

        try:
            db.session.query(UserTodoListTbl).filter_by(todolist_id=todolist_id).filter_by(user_id=user_id).delete()
            if role:
                db.session.add(UserTodoListTbl(todolist_id=todolist_id, user_id=user_id, role=role))

            if role and role == 'owner':
                db.session.query(UserTodoListTbl).filter_by(todolist_id=todolist_id).filter_by(user_id=self.user_id). \
                    delete()
                if new_owner_role:
                    db.session.add(UserTodoListTbl(todolist_id=todolist_id, user_id=self.user_id, role=new_owner_role))
            db.session.commit()
            return True
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return
