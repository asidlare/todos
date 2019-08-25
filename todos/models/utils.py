from sqlalchemy import Table
from sqlalchemy import DDL
from sqlalchemy.event import listen
from functools import partial


def on_create(class_name, sqltext):

    ddl = DDL(sqltext)

    def listener(tablename, ddl, table, bind, **kw):
        if table.name == tablename:
            ddl(table, bind, **kw)

    listen(Table,
           'after_create',
           partial(listener, class_name.__table__.name, ddl))


def on_drop(class_name, sqltext):

    ddl = DDL(sqltext)

    def listener(tablename, ddl, table, bind, **kw):
        if table.name == tablename:
            ddl(table, bind, **kw)

    listen(Table,
           'before_drop',
           partial(listener, class_name.__table__.name, ddl))
