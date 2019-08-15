from tests.base import IntegrationTestCase
from todos.models.api.user_api import UserApi


class UserViewTests(IntegrationTestCase):

    def setUp(self):
        super().setUp()

        self.user_api = UserApi()

        # register user
        self.client.post('/api/v1/user', json={
            'login': 'user1',
            'name': 'Test User',
            'password': 'abc123',
            'email': 'user1@example.com',
        })

        # try to log using correct password
        self.client.post('/api/v1/login', json={'login': 'user1', 'password': 'abc123'})

    def test_get(self):
        result = self.client.get('/api/v1/user')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['login'], 'user1')

        # log out
        self.client.get('/api/v1/logout')

    def test_post(self):
        # new user with the same login
        result = self.client.post('/api/v1/user', json={
            'login': 'user1',
            'name': 'Test User',
            'password': 'abc123',
            'email': 'user1@hurra.com',
        })
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.json['error'], 'Login exists')

        # new user with the same email
        result = self.client.post('/api/v1/user', json={
            'login': 'user2',
            'name': 'Test User',
            'password': 'abc123',
            'email': 'user1@example.com',
        })
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.json['error'], 'Email exists')

        # new user
        result = self.client.post('/api/v1/user', json={
            'login': 'user2',
            'name': 'Test User',
            'password': 'abc123',
            'email': 'user2@example.com',
        })
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.json['login'], 'user2')

        # log out
        self.client.get('/api/v1/logout')

    def test_patch_no_data(self):
        # patch with empty json
        result = self.client.patch('/api/v1/user', json=None)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.json['error'], 'Request with no data to change')

        # log out
        self.client.get('/api/v1/logout')

    def test_patch_name(self):
        # check name before request
        user = self.user_api.read_user_by_login('user1')
        self.assertEqual(user.name, 'Test User')

        result = self.client.patch('/api/v1/user', json={'name': 'User 1'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['response'], 'User user1 updated')

        # check name after request
        user = self.user_api.read_user_by_login('user1')
        self.assertEqual(user.name, 'User 1')

        # log out
        self.client.get('/api/v1/logout')

    def test_patch_password(self):
        # check name before request
        user = self.user_api.read_user_by_login('user1')
        self.assertEqual(user.password, 'abc123')
        self.assertNotEqual(user.password, 'abc12')

        result = self.client.patch('/api/v1/user', json={'password': 'test123'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['response'], 'User user1 updated')

        # check name after request
        user = self.user_api.read_user_by_login('user1')
        self.assertEqual(user.password, 'test123')

        # log out
        self.client.get('/api/v1/logout')

    def test_patch_email(self):
        # check name before request
        user = self.user_api.read_user_by_login('user1')
        self.assertEqual(user.email, 'user1@example.com')

        # changed to not correct email
        result = self.client.patch('/api/v1/user', json={'email': 'test123'})
        self.assertEqual(result.status_code, 409)
        self.assertEqual(result.json['error'], {'email': ['Not a valid email address.']})

        # changed to correct email
        result = self.client.patch('/api/v1/user', json={'email': 'test123@example.com'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['response'], 'User user1 updated')

        # check name after request
        user = self.user_api.read_user_by_login('user1')
        self.assertEqual(user.email, 'test123@example.com')

        # log out
        self.client.get('/api/v1/logout')

    def test_patch_name_and_email_together(self):
        # check name before request
        user = self.user_api.read_user_by_login('user1')
        self.assertEqual(user.email, 'user1@example.com')
        self.assertEqual(user.name, 'Test User')

        # changed to correct name and email
        result = self.client.patch('/api/v1/user', json={'name': 'User 1', 'email': 'test123@example.com'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['response'], 'User user1 updated')

        # check name after request
        user = self.user_api.read_user_by_login('user1')
        self.assertEqual(user.email, 'test123@example.com')
        self.assertEqual(user.name, 'User 1')

        # log out
        self.client.get('/api/v1/logout')

    def test_delete(self):
        # check object before request
        user = self.user_api.read_user_by_login('user1')
        self.assertNotEqual(user, None)

        # changed to correct name and email
        result = self.client.delete('/api/v1/user')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['response'], 'User user1 deleted')

        # check object after request
        user = self.user_api.read_user_by_login('user1')
        self.assertEqual(user, None)
