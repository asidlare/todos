from tests.base import IntegrationTestCase
from todos.models.api.user_api import UserApi
from todos.models.definitions import db, RoleTbl, TodoListTbl


class TodoListViewTests(IntegrationTestCase):

    def setUp(self):
        super().setUp()

        owner = RoleTbl(role='owner', change_owner=1, delete=1, change_permissions=1, change_data=1, read=1,
                        todolist_count_limit=10, task_count_limit=100, task_depth_limit=10)
        admin = RoleTbl(role='admin', change_owner=0, delete=0, change_permissions=0, change_data=1, read=1,
                        task_count_limit=80, task_depth_limit=8)
        reader = RoleTbl(role='reader', change_owner=0, delete=0, change_permissions=0, change_data=0, read=1)
        db.session.add(owner)
        db.session.add(admin)
        db.session.add(reader)
        db.session.commit()

        self.user_api = UserApi()

        # register users
        self.client.post('/api/v1/user', json={
            'login': 'user1',
            'name': 'Test User',
            'password': 'abc123',
            'email': 'user1@example.com',
        })
        self.client.post('/api/v1/user', json={
            'login': 'user2',
            'name': 'Test User',
            'password': 'abc123',
            'email': 'user2@example.com',
        })
        self.client.post('/api/v1/user', json={
            'login': 'user3',
            'name': 'Test User',
            'password': 'abc123',
            'email': 'user3@example.com',
        })

        # try to log as user 1 using correct password
        self.client.post('/api/v1/login', json={'login': 'user1', 'password': 'abc123'})

    def create_todolist_set(self):
        self.client.post('/api/v1/todolists', json={'label': 'List 1', 'status': 'active', 'priority': 'high'})
        self.client.post('/api/v1/todolists', json={'label': 'List 2', 'status': 'inactive', 'priority': 'medium'})
        self.client.post('/api/v1/todolists', json={'label': 'List 4', 'status': 'active', 'priority': 'medium'})
        self.client.post('/api/v1/todolists', json={'label': 'List 3', 'status': 'active', 'priority': 'medium'})
        self.client.post('/api/v1/todolists', json={'label': 'List 5', 'status': 'inactive', 'priority': 'veryhigh'})
        self.client.post('/api/v1/todolists', json={'label': 'List 6', 'status': 'active', 'priority': 'veryhigh'})

    def test_post(self):
        # new user with the same login
        result = self.client.post('/api/v1/todolists', json={
            'label': 'List 1',
            'status': 'active',
            'priority': 'medium',
        })
        self.assertEqual(result.status_code, 201)

        # not correct status
        result = self.client.post('/api/v1/todolists', json={
            'label': 'List 1',
            'status': 'inny',
            'priority': 'medium',
        })
        self.assertEqual(result.status_code, 409)

        # not correct priority
        result = self.client.post('/api/v1/todolists', json={
            'label': 'List 1',
            'status': 'active',
            'priority': 'inne',
        })
        self.assertEqual(result.status_code, 409)

        # log out
        self.client.get('/api/v1/logout')

    def test_get(self):
        # all todolists - no one found
        result = self.client.get('/api/v1/todolists')
        self.assertEqual(result.status_code, 404)

        self.create_todolist_set()

        # all todolists
        result = self.client.get('/api/v1/todolists')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in result.json],
            [
                {'label': 'List 6', 'priority': 'veryhigh', 'status': 'active'},
                {'label': 'List 5', 'priority': 'veryhigh', 'status': 'inactive'},
                {'label': 'List 1', 'priority': 'high', 'status': 'active'},
                {'label': 'List 3', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 4', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 2', 'priority': 'medium', 'status': 'inactive'}
            ]
        )

        # all todolists filtered by priority medium
        result = self.client.get('/api/v1/todolists?priority=medium')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in result.json],
            [
                {'label': 'List 3', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 4', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 2', 'priority': 'medium', 'status': 'inactive'}
            ]
        )

        # all todolists filtered by priority medium and status active
        result = self.client.get('/api/v1/todolists?priority=medium&status=active')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in result.json],
            [
                {'label': 'List 3', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 4', 'priority': 'medium', 'status': 'active'},
            ]
        )

        # all todolists filtered by priority medium and status active and label List 3
        result = self.client.get('/api/v1/todolists?priority=medium&status=active&label=List%203')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in result.json],
            [
                {'label': 'List 3', 'priority': 'medium', 'status': 'active'},
            ]
        )

        todo = db.session.query(TodoListTbl).filter_by(label='List 3').first()

        # all todolists filtered by todolist_id
        result = self.client.get(f"/api/v1/todolists?todolist_id={todo.todolist_id}")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in result.json],
            [
                {'label': 'List 3', 'priority': 'medium', 'status': 'active'},
            ]
        )

        # log out
        self.client.get('/api/v1/logout')

    def test_patch(self):
        self.create_todolist_set()

        todo = db.session.query(TodoListTbl).filter_by(label='List 3').first()
        self.assertEqual(
            [{'login': row['login'], 'role': row['role']} for row in todo.all_roles],
            [{'login': 'user1', 'role': 'owner'}]
        )

        # empty json
        result = self.client.patch(f"/api/v1/todolists/{todo.todolist_id}")
        self.assertEqual(result.status_code, 400)

        # empty json
        result = self.client.patch(f"/api/v1/todolists/{todo.todolist_id}",
                                   json={'label': 'List 7', 'description': 'Desc',
                                         'priority': 'high', 'status': 'active'})
        self.assertEqual(result.status_code, 200)

        # not correct priority
        result = self.client.patch(f"/api/v1/todolists/{todo.todolist_id}",
                                   json={'label': 'List 7', 'description': 'Desc',
                                         'priority': 'high1', 'status': 'active'})
        self.assertEqual(result.status_code, 409)

        # not correct status
        result = self.client.patch(f"/api/v1/todolists/{todo.todolist_id}",
                                   json={'label': 'List 7', 'description': 'Desc',
                                         'priority': 'high', 'status': 'active1'})
        self.assertEqual(result.status_code, 409)

        # log out
        self.client.get('/api/v1/logout')

    def test_patch_and_delete_with_permissions(self):
        self.create_todolist_set()

        todo = db.session.query(TodoListTbl).filter_by(label='List 3').first()
        self.assertEqual(
            [{'login': row['login'], 'role': row['role']} for row in todo.all_roles],
            [{'login': 'user1', 'role': 'owner'}]
        )

        # set owner to user2 and reader to user1 and try to update list
        result = self.client.put(
            f"/api/v1/todolists/permissions/{todo.todolist_id}/user2@example.com?role=owner&new_owner_role=reader")
        self.assertEqual(result.status_code, 200)

        todo = db.session.query(TodoListTbl).filter_by(todolist_id=todo.todolist_id).first()
        self.assertEqual(
            sorted([(row['login'], row['role']) for row in todo.all_roles]),
            [('user1', 'reader'), ('user2', 'owner')]
        )

        # try to patch
        result = self.client.patch(f"/api/v1/todolists/{todo.todolist_id}", json={'label': 'List 8'})
        self.assertEqual(result.status_code, 403)

        # try to delete
        result = self.client.delete(f"/api/v1/todolists/{todo.todolist_id}")
        self.assertEqual(result.status_code, 403)

        # try to repeat setting owner to user2 and reader to user1 and try to update list
        result = self.client.put(
            f"/api/v1/todolists/permissions/{todo.todolist_id}/user2@example.com?role=owner&new_owner_role=reader")
        self.assertEqual(result.status_code, 403)

        todo = db.session.query(TodoListTbl).filter_by(label='List 4').first()

        # set owner to user2 and no access to user1 and try to update list
        result = self.client.put(
            f"/api/v1/todolists/permissions/{todo.todolist_id}/user2@example.com?role=owner")
        self.assertEqual(result.status_code, 200)

        todo = db.session.query(TodoListTbl).filter_by(todolist_id=todo.todolist_id).first()
        self.assertEqual(
            [{'login': row['login'], 'role': row['role']} for row in todo.all_roles],
            [{'login': 'user2', 'role': 'owner'}]
        )

        # try to patch
        result = self.client.patch(f"/api/v1/todolists/{todo.todolist_id}", json={'label': 'List 8'})
        self.assertEqual(result.status_code, 404)

        # try to delete
        result = self.client.delete(f"/api/v1/todolists/{todo.todolist_id}")
        self.assertEqual(result.status_code, 404)

        # try to repeat setting owner to user2 and no access to user1 and try to update list
        result = self.client.put(
            f"/api/v1/todolists/permissions/{todo.todolist_id}/user2@example.com?role=owner")
        self.assertEqual(result.status_code, 404)

        # log out
        self.client.get('/api/v1/logout')

    def test_delete(self):
        self.create_todolist_set()

        todo = db.session.query(TodoListTbl).filter_by(label='List 3').first()

        result = self.client.delete(f"/api/v1/todolists/{todo.todolist_id}")
        self.assertEqual(result.status_code, 200)

        todo = db.session.query(TodoListTbl).filter_by(label='List 3').first()
        self.assertEqual(todo, None)

        # log out
        self.client.get('/api/v1/logout')

    def test_put_errors(self):
        self.create_todolist_set()

        todo = db.session.query(TodoListTbl).filter_by(label='List 3').first()

        # user1 own email
        result = self.client.put(
            f"/api/v1/todolists/permissions/{todo.todolist_id}/user1@example.com")
        self.assertEqual(result.status_code, 403)

        # unknown email
        result = self.client.put(
            f"/api/v1/todolists/permissions/{todo.todolist_id}/user4@example.com")
        self.assertEqual(result.status_code, 404)

        # log out
        self.client.get('/api/v1/logout')
