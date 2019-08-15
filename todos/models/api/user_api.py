from uuid import uuid4
import logging
from datetime import datetime
from todos.models.definitions import db, UserTbl
from sqlalchemy.exc import DBAPIError, SQLAlchemyError


logger = logging.getLogger('todos')


class UserApi():

    def read_user_by_user_id(self, user_id):
        return db.session.query(UserTbl).filter_by(user_id=user_id).first()

    def read_user_by_login(self, login):
        return db.session.query(UserTbl).filter_by(login=login).first()

    def read_user_by_email(self, email):
        return db.session.query(UserTbl).filter_by(email=email).first()

    def create_user(self, data):
        try:
            user = UserTbl(**data, user_id=str(uuid4()), created=datetime.utcnow())
            db.session.add(user)
            db.session.commit()
            return user
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return

    def update_user(self, user_id, to_change):
        try:
            db.session.query(UserTbl).filter_by(user_id=user_id).update(to_change)
            db.session.commit()
            return True
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback()
            return

    def delete_user(self, user_id):
        try:
            db.session.query(UserTbl).filter_by(user_id=user_id).delete()
            db.session.commit()
            return True
        except (DBAPIError, SQLAlchemyError) as e:
            logger.error(f"Database error: {e}")
            db.session.rollback
            return
