from .base import db, DictMixin, DATETIME_TYPE
from sqlalchemy_utils import PasswordType, EmailType, force_auto_coercion
from flask_login import UserMixin

force_auto_coercion()


class UserTbl(db.Model, UserMixin, DictMixin):
    __tablename__ = 'User'

    __str__ = lambda self: str(self.to_dict()) # noqa
    __repr__ = lambda self: repr(self.to_dict()) # noqa

    user_id = db.Column(db.CHAR(36), primary_key=True)
    login = db.Column(db.String(length=80), nullable=False, unique=True)
    password = db.Column(PasswordType(schemes=['pbkdf2_sha512']), nullable=False)
    name = db.Column(db.String(length=255), nullable=False)
    email = db.Column(EmailType, nullable=False, unique=True)
    created = db.Column(DATETIME_TYPE, nullable=False)

    def get_id(self):
        """Return user_id per login"""
        return self.user_id

    def is_authenticated(self, login, password):
        """Return True if valid credentials provided"""
        if self.login == login and self.password == password:
            return True
        return False

    def to_dict(self):
        out = dict()
        for key in ('login', 'user_id', 'name', 'email', 'created'):
            out[key] = getattr(self, key)
        return out
