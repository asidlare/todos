from tests.base import IntegrationTestCase
from todos.models.api.user_api import UserApi
from todos.models.definitions import db, RoleTbl, TodoListTbl


class TodoListViewTests(IntegrationTestCase):

    def setUp(self):
        super().setUp()

        owner = RoleTbl(role='owner', change_owner=1, delete=1, change_permissions=1, change_data=1, read=1)
        admin = RoleTbl(role='admin', change_owner=0, delete=0, change_permissions=0, change_data=1, read=1)
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

        # try to log as user 1 using correct password
        self.client.post('/api/v1/login', json={'login': 'user1', 'password': 'abc123'})

        # create todolist
        self.client.post('/api/v1/todolists', json={'label': 'List 1', 'status': 'active', 'priority': 'high'})
        self.todolist = db.session.query(TodoListTbl).filter_by(label='List 1').first()

    def create_tasks_set(self):
        """
                                                  tree structure for testing
                                                  
                                                    'Task 0'(high, active)                 'Task 2'(veryhigh, done)
                                                            /\                                     |
                                                           /  \                                    |
                                   'Task 1'(medium, active)    'Task 6'(high, active)      'Task 7'(medium, done)
                                   /        |              \                                       
                                  /         |               \                                      
                                 /          |                \                                     
                                /           |                 \                                    
            'Task 3'(high, done)    'Task 4'(medium, active)   'Task 5'(medium, active)
                    |                       |
                    |                       |
            'Task 8'(medium, done)  'Task 9'(medium, active)
        """ # noqa
        task0 = self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}",
                                 json={'label': 'Task 0', 'status': 'active',
                                       'priority': 'high', 'parent_id': None})
        task1 = self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}",
                                 json={'label': 'Task 1', 'status': 'active',
                                       'priority': 'medium', 'parent_id': task0.json['task_id']})
        task2 = self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}",
                                 json={'label': 'Task 2', 'status': 'done',
                                       'priority': 'veryhigh', 'parent_id': None})
        task3 = self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}",
                                 json={'label': 'Task 3', 'status': 'done',
                                       'priority': 'high', 'parent_id': task1.json['task_id']})
        task4 = self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}",
                                 json={'label': 'Task 4', 'status': 'active',
                                       'priority': 'medium', 'parent_id': task1.json['task_id']})
        self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}",
                         json={'label': 'Task 5', 'status': 'active',
                               'priority': 'medium', 'parent_id': task1.json['task_id']})
        self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}",
                         json={'label': 'Task 6', 'status': 'active',
                               'priority': 'high', 'parent_id': task0.json['task_id']})
        self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}",
                         json={'label': 'Task 7', 'status': 'done',
                               'priority': 'medium', 'parent_id': task2.json['task_id']})
        self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}",
                         json={'label': 'Task 8', 'status': 'done',
                               'priority': 'medium', 'parent_id': task3.json['task_id']})
        self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}",
                         json={'label': 'Task 9', 'status': 'active',
                               'priority': 'medium', 'parent_id': task4.json['task_id']})
        return [task0.json, task1.json, task2.json]

    def test_post(self):
        # correct data
        result = self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}", json={
            'label': 'List 1',
            'status': 'active',
            'priority': 'medium',
        })
        self.assertEqual(result.status_code, 201)

        # not correct status
        result = self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}", json={
            'label': 'List 1',
            'status': 'inny',
            'priority': 'medium',
        })
        self.assertEqual(result.status_code, 409)

        # not correct priority
        result = self.client.post(f"/api/v1/tasks/{self.todolist.todolist_id}", json={
            'label': 'List 1',
            'status': 'active',
            'priority': 'inne',
        })
        self.assertEqual(result.status_code, 409)

        # log out
        self.client.get('/api/v1/logout')

    def test_get(self):
        # all todolists - no one found
        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}")
        self.assertEqual(result.status_code, 404)

        tasks = self.create_tasks_set()

        # tree from dfs algorithm
        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}?expand=true")
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in result.json],
            [
                {'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 7', 'priority': 'medium', 'status': 'done', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
                {'label': 'Task 3', 'priority': 'high', 'status': 'done', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 8', 'priority': 'medium', 'status': 'done', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': True}
            ]
        )

        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}?expand=false")
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in result.json],
            [
                {'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
            ]
        )

        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}"
                                 f"?expand=true&task_id={tasks[0]['task_id']}")
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in result.json],
            [
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
                {'label': 'Task 3', 'priority': 'high', 'status': 'done', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 8', 'priority': 'medium', 'status': 'done', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': True}
            ]
        )

        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}"
                                 f"?expand=false&task_id={tasks[0]['task_id']}")
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in result.json],
            [
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
            ]
        )

        # log out
        self.client.get('/api/v1/logout')

    def test_patch(self):
        tasks = self.create_tasks_set()

        # empty json
        result = self.client.patch(f"/api/v1/tasks/{self.todolist.todolist_id}/{tasks[1]['task_id']}")
        self.assertEqual(result.status_code, 400)

        # empty json
        result = self.client.patch(f"/api/v1/tasks/{self.todolist.todolist_id}/{tasks[1]['task_id']}",
                                   json={'label': 'Task 10', 'description': 'Desc',
                                         'priority': 'high', 'status': 'active'})
        self.assertEqual(result.status_code, 200)

        # not correct priority
        result = self.client.patch(f"/api/v1/tasks/{self.todolist.todolist_id}/{tasks[1]['task_id']}",
                                   json={'label': 'List 7', 'description': 'Desc',
                                         'priority': 'high1', 'status': 'active'})
        self.assertEqual(result.status_code, 409)

        # not correct status
        result = self.client.patch(f"/api/v1/tasks/{self.todolist.todolist_id}/{tasks[1]['task_id']}",
                                   json={'label': 'List 7', 'description': 'Desc',
                                         'priority': 'high', 'status': 'active1'})
        self.assertEqual(result.status_code, 409)

        # log out
        self.client.get('/api/v1/logout')

    def test_delete_task(self):
        tasks = self.create_tasks_set()

        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}?expand=true")

        # tree before deleting
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in result.json],
            [
                {'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 7', 'priority': 'medium', 'status': 'done', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
                {'label': 'Task 3', 'priority': 'high', 'status': 'done', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 8', 'priority': 'medium', 'status': 'done', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': True}
            ]
        )

        self.client.delete(f"/api/v1/tasks/{self.todolist.todolist_id}"
                           f"?action=delete&task_id={tasks[1]['task_id']}")

        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}?expand=true")

        # tree after deleting
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in result.json],
            [
                {'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 7', 'priority': 'medium', 'status': 'done', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
            ]
        )

        # log out
        self.client.get('/api/v1/logout')

    def test_purge(self):
        self.create_tasks_set()

        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}?expand=true")

        # tree before purging
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in result.json],
            [
                {'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 7', 'priority': 'medium', 'status': 'done', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
                {'label': 'Task 3', 'priority': 'high', 'status': 'done', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 8', 'priority': 'medium', 'status': 'done', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': True}
            ]
        )

        self.client.delete(f"/api/v1/tasks/{self.todolist.todolist_id}?action=purge")
        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}?expand=true")

        # tree after purging
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in result.json],
            [
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': True}
            ]
        )

    def test_reparent(self):
        tasks = self.create_tasks_set()

        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}?expand=true")

        # initial tree
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in result.json],
            [
                {'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 7', 'priority': 'medium', 'status': 'done', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
                {'label': 'Task 3', 'priority': 'high', 'status': 'done', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 8', 'priority': 'medium', 'status': 'done', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': True}
            ]
        )

        # nothing changed, bad parent
        self.client.put(f"/api/v1/tasks/reparent/{self.todolist.todolist_id}/{tasks[1]['task_id']}"
                        f"?new_parent_id={tasks[1]['task_id']}")
        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}?expand=true")

        # initial tree, nothing changed
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in result.json],
            [
                {'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 7', 'priority': 'medium', 'status': 'done', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
                {'label': 'Task 3', 'priority': 'high', 'status': 'done', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 8', 'priority': 'medium', 'status': 'done', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': True}
            ]
        )

        # nothing changed, bad parent
        self.client.put(f"/api/v1/tasks/reparent/{self.todolist.todolist_id}/{tasks[1]['task_id']}"
                        f"?new_parent_id={tasks[2]['task_id']}")
        result = self.client.get(f"/api/v1/tasks/{self.todolist.todolist_id}?expand=true")

        # initial tree, nothing changed
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in result.json],
            [
                {'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
                {'label': 'Task 3', 'priority': 'high', 'status': 'done', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 8', 'priority': 'medium', 'status': 'done', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': True},
                {'label': 'Task 7', 'priority': 'medium', 'status': 'done', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True}
            ]
        )
