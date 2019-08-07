import os
import unittest
from flask_sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection

from todos import Todos
from todos.models import db


class TestCaseWithDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["FLASK_ENV"] = "testing"  # Force using config.testing

    @classmethod
    def tearDownClass(cls):
        del os.environ["FLASK_ENV"]  # Cleanup app environment

    def setUp(self):
        self.app_context = Todos().app.app_context()
        with self.app_context:
            @event.listens_for(Engine, "connect")
            def connect(dbapi_connection, connection_record):
                if isinstance(dbapi_connection, Connection):
                    cursor = dbapi_connection.cursor()
                    cursor.execute('PRAGMA foreign_keys=ON;')
                    cursor.execute('PRAGMA encoding="UTF-8";')
                    cursor.close()
        self.app_context.push()
        self.db = db
        self.db.create_all()

    def tearDown(self):
        self.db.drop_all()
        self.app_context.pop()


class IntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["FLASK_ENV"] = "testing"  # Force using config.testing

    @classmethod
    def tearDownClass(cls):
        del os.environ["FLASK_ENV"]  # Cleanup app environment

    def setUp(self):
        self.app = Todos().app
        self.app.testing = True
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        with self.app_context:
            @event.listens_for(Engine, "connect")
            def connect(dbapi_connection, connection_record):
                if isinstance(dbapi_connection, Connection):
                    cursor = dbapi_connection.cursor()
                    cursor.execute('PRAGMA foreign_keys=ON;')
                    cursor.execute('PRAGMA encoding="UTF-8";')
                    cursor.close()
        self.app_context.push()
        self.db = db
        self.db.create_all()

    def tearDown(self):
        self.db.drop_all()
        self.app_context.pop()
