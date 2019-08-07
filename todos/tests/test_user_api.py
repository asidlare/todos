from uuid import uuid4
from datetime import datetime
from tests.base import TestCaseWithDB
from todos.models.api.user_api import UserApi
from todos.models.definitions import db, UserTbl


class UserApiTests(TestCaseWithDB):

    def setUp(self):
        super().setUp()

        self.user_id = str(uuid4())
        self.created = datetime.utcnow()
        self.user = UserTbl(user_id=self.user_id, login='user1', password='abc123', name='Test User',
                            email='abc@example.com', created=self.created)
        db.session.add(self.user)
        db.session.commit()

        self.user_api = UserApi()

    def test_read_by_user_id(self):
        result = self.user_api.read_user_by_user_id(self.user_id)
        self.assertEqual(
            result.to_dict(),
            {
                'login': 'user1',
                'user_id': self.user_id,
                'name': 'Test User',
                'email': 'abc@example.com',
                'created': self.created,
            }
        )

    def test_read_by_login(self):
        result = self.user_api.read_user_by_login('user1')
        self.assertEqual(
            result.to_dict(),
            {
                'login': 'user1',
                'user_id': self.user_id,
                'name': 'Test User',
                'email': 'abc@example.com',
                'created': self.created
            }
        )

    def test_read_by_email(self):
        result = self.user_api.read_user_by_email('abc@example.com')
        self.assertEqual(
            result.to_dict(),
            {
                'login': 'user1',
                'user_id': self.user_id,
                'name': 'Test User',
                'email': 'abc@example.com',
                'created': self.created
            }
        )

    def test_create_user(self):
        # repeated login
        data = {
            'login': 'user1',
            'name': 'Test User',
            'password': 'user123',
            'email': 'user2@example.com'
        }

        result = self.user_api.create_user(data)
        self.assertEqual(result, None)

        # repeated email
        data = {
            'login': 'user2',
            'name': 'Test User',
            'password': 'user123',
            'email': 'abc@example.com'
        }

        result = self.user_api.create_user(data)
        self.assertEqual(result, None)

        # correct entry
        data = {
            'login': 'user2',
            'name': 'Test User 2',
            'password': 'user123',
            'email': 'user2@example.com'
        }

        result = self.user_api.create_user(data)
        self.assertEqual(
            (result.login, result.name, result.email),
            ('user2', 'Test User 2', 'user2@example.com')
        )

    def test_update_user(self):
        # correct entry
        data = {
            'login': 'user2',
            'name': 'Test User 2',
            'password': 'user123',
            'email': 'user2@example.com'
        }

        result = self.user_api.create_user(data)
        self.assertEqual(
            (result.login, result.name, result.email),
            ('user2', 'Test User 2', 'user2@example.com')
        )

        # update to repeated email
        result = self.user_api.update_user(self.user_id, {'email': 'user2@example.com'})
        self.assertEqual(result, None)

        # update to not repeated email
        result = self.user_api.update_user(self.user_id, {'email': 'user1@example.com'})
        self.assertEqual(result, True)

    def test_delete_user(self):
        result = self.user_api.read_user_by_user_id(self.user_id)
        self.assertNotEqual(result, None)

        self.user_api.delete_user(self.user_id)
        result = self.user_api.read_user_by_user_id(self.user_id)
        self.assertEqual(result, None)
