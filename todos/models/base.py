from sqlalchemy import MetaData, DateTime, Boolean, Integer, SmallInteger
from sqlalchemy.dialects import mysql
from flask_sqlalchemy import SQLAlchemy as _BaseSQLAlchemy
from flask_migrate import Migrate

# Recommended naming convensions to make possible to autogenerate migrations
# See http://alembic.zzzcomputing.com/en/latest/naming.html
NAMING_CONVENSION = {
    "ix": 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(column_0_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s'
}

# Prevent constant migrations from sa.DateTime(timezone=True) to mysql.DATETIME().
DATETIME_TYPE = DateTime(timezone=True)
DATETIME_TYPE = DATETIME_TYPE.with_variant(mysql.DATETIME(), 'mysql')
# mysql boolean
BOOLEAN_TYPE = Boolean()
BOOLEAN_TYPE = BOOLEAN_TYPE.with_variant(mysql.TINYINT(display_width=1), 'mysql')
# Unsigned integer.
UNSIGNEDINT_TYPE = Integer()
UNSIGNEDINT_TYPE = UNSIGNEDINT_TYPE.with_variant(mysql.INTEGER(unsigned=True), 'mysql')
# Unsigned integer.
UNSIGNEDSMALLINT_TYPE = SmallInteger()
UNSIGNEDSMALLINT_TYPE = UNSIGNEDSMALLINT_TYPE.with_variant(mysql.SMALLINT(unsigned=True), 'mysql')


# The “pre ping” feature will normally emit SQL equivalent to “SELECT 1” each time a connection is checked out
# from the pool; if an error is raised that is detected as a “disconnect” situation, the connection will be
# immediately recycled, and all other pooled connections older than the current time are invalidated, so that
# the next time they are checked out, they will also be recycled before use.
class SQLAlchemy(_BaseSQLAlchemy):
    def apply_pool_defaults(self, app, options):
        super(SQLAlchemy, self).apply_pool_defaults(app, options)
        options["pool_pre_ping"] = True


db = SQLAlchemy(metadata=MetaData(naming_convention=NAMING_CONVENSION))
migrate = Migrate(db=db)


class DictMixin:
    def to_dict(self):
        return dict((column.name, getattr(self, column.name)) for column in self.__table__.columns)
