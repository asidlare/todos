from tests.base import IntegrationTestCase


class LoginTests(IntegrationTestCase):

    def test_loging_and_logout(self):
        # register user
        result = self.client.post('/api/v1/user', json={
            'login': 'user1',
            'name': 'Test User',
            'password': 'abc123',
            'email': 'user1@example.com',
        })
        self.assertEqual(result.status_code, 201)
        self.assertTrue(result.json)
        self.assertEqual(result.json['login'], 'user1')

        # try to get user without logging
        result = self.client.get('/api/v1/user')
        self.assertEqual(result.status_code, 403)

        # try to log using login only
        result = self.client.post('/api/v1/login', json={'login': 'user1'})
        self.assertEqual(result.status_code, 500)
        # try to log using password only
        result = self.client.post('/api/v1/login', json={'password': 'abc123'})
        self.assertEqual(result.status_code, 500)
        # try to log using bad password
        result = self.client.post('/api/v1/login', json={'login': 'user1', 'password': 'abc1234'})
        self.assertEqual(result.status_code, 404)

        # try to log using correct password
        result = self.client.post('/api/v1/login', json={'login': 'user1', 'password': 'abc123'})
        self.assertEqual(result.status_code, 200)

        # try to get user after logging in
        result = self.client.get('/api/v1/user')
        self.assertEqual(result.status_code, 200)

        # log out
        result = self.client.get('/api/v1/logout')
        self.assertEqual(result.status_code, 200)

        # try to get user after logging out
        result = self.client.get('/api/v1/user')
        self.assertEqual(result.status_code, 403)
