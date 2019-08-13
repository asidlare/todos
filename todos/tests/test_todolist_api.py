from uuid import uuid4
from datetime import datetime
from tests.base import TestCaseWithDB
from todos.models.definitions import (db, UserTbl, TodoListTbl, RoleTbl, Priority, TodoListStatus)
from todos.models.api.todolists_api import TodoListApi


class TodoListApiTests(TestCaseWithDB):

    def setUp(self):
        super().setUp()

        self.user = UserTbl(user_id=str(uuid4()), login='user1', password='abc123', name='Test User 1',
                            email='user1@example.com', created=datetime.utcnow())
        db.session.add(self.user)
        db.session.commit()
        owner = RoleTbl(role='owner', change_owner=1, delete=1, change_permissions=1, change_data=1, read=1)
        admin = RoleTbl(role='admin', change_owner=0, delete=0, change_permissions=0, change_data=1, read=1)
        reader = RoleTbl(role='reader', change_owner=0, delete=0, change_permissions=0, change_data=0, read=1)
        db.session.add(owner)
        db.session.add(admin)
        db.session.add(reader)
        db.session.commit()

        self.todolist_api = TodoListApi(self.user.user_id)

    def create_todolist_set(self):
        self.todolist_api.create_todolist({'label': 'List 1', 'status': TodoListStatus.active.name,
                                           'priority': Priority.high.value})
        self.todolist_api.create_todolist({'label': 'List 2', 'status': TodoListStatus.inactive.name,
                                           'priority': Priority.medium.value})
        self.todolist_api.create_todolist({'label': 'List 4', 'status': TodoListStatus.active.name,
                                           'priority': Priority.medium.value})
        self.todolist_api.create_todolist({'label': 'List 3', 'status': TodoListStatus.active.name,
                                           'priority': Priority.medium.value})
        self.todolist_api.create_todolist({'label': 'List 5', 'status': TodoListStatus.inactive.name,
                                           'priority': Priority.veryhigh.value})
        self.todolist_api.create_todolist({'label': 'List 6', 'status': TodoListStatus.active.name,
                                           'priority': Priority.veryhigh.value})

    def test_create_todolist(self):
        todo = self.todolist_api.create_todolist({'label': 'List1', 'status': TodoListStatus.active.name,
                                                  'priority': Priority.medium.value})

        self.assertEqual(
            [(row['label'], row['priority'], row['status']) for row in self.user.all_todolists()],
            [('List1', 'medium', 'active')]
        )

        self.assertEqual(
            [(change['changed_by'], change['status'])for change in todo.status_changes],
            [('Test User 1', 'active')]
        )

        self.assertEqual(
            todo.all_roles,
            [{'login': 'user1', 'name': 'Test User 1', 'email': 'user1@example.com', 'role': 'owner'}]
        )

        self.assertEqual(todo.creator, self.user.user_id)

        todo_fetched = self.todolist_api.read_todolist_by_id(todo.todolist_id)

        self.assertEqual(todo, todo_fetched)

    def test_get_todo_lists(self):
        self.create_todolist_set()

        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in self.todolist_api.get_todolists(filters={})],
            [
                {'label': 'List 6', 'priority': 'veryhigh', 'status': 'active'},
                {'label': 'List 5', 'priority': 'veryhigh', 'status': 'inactive'},
                {'label': 'List 1', 'priority': 'high', 'status': 'active'},
                {'label': 'List 3', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 4', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 2', 'priority': 'medium', 'status': 'inactive'}
            ]
        )

        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in self.todolist_api.get_todolists(filters={'priority': 'medium'})],
            [
                {'label': 'List 3', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 4', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 2', 'priority': 'medium', 'status': 'inactive'}
            ]
        )

        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in self.todolist_api.get_todolists(filters={'priority': 'medium', 'status': 'active'})],
            [
                {'label': 'List 3', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 4', 'priority': 'medium', 'status': 'active'},
            ]
        )

        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in self.todolist_api.get_todolists(filters={'priority': 'medium', 'status': 'active',
                                                                 'label': 'List 4'})],
            [
                {'label': 'List 4', 'priority': 'medium', 'status': 'active'},
            ]
        )

        todo = db.session.query(TodoListTbl).filter_by(label='List 3').first()

        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in self.todolist_api.get_todolists(todolist_id=todo.todolist_id)],
            [
                {'label': 'List 3', 'priority': 'medium', 'status': 'active'},
            ]
        )

    def test_update_todo_lists(self):
        self.create_todolist_set()

        todo = db.session.query(TodoListTbl).filter_by(label='List 3').first()

        self.assertEqual(
            [{'label': row['label'], 'description': row['description'], 'priority': row['priority'],
              'status': row['status'], 'saved_status': status['status'], 'changed_by': status['changed_by']}
             for row in self.todolist_api.get_todolists(todolist_id=todo.todolist_id)
             for status in row['status_changes']],
            [
                {'label': 'List 3', 'description': None, 'priority': 'medium', 'status': 'active',
                 'saved_status': 'active', 'changed_by': 'Test User 1'},
            ]
        )

        self.todolist_api.update_todolist(todo.todolist_id, {'label': 'List 7'})
        self.assertEqual(
            [{'label': row['label'], 'description': row['description'], 'priority': row['priority'],
              'status': row['status'], 'saved_status': status['status'], 'changed_by': status['changed_by']}
             for row in self.todolist_api.get_todolists(todolist_id=todo.todolist_id)
             for status in row['status_changes']],
            [
                {'label': 'List 7', 'description': None, 'priority': 'medium', 'status': 'active',
                 'saved_status': 'active', 'changed_by': 'Test User 1'},
            ]
        )

        self.todolist_api.update_todolist(todo.todolist_id, {'description': 'This is List 7'})
        self.assertEqual(
            [{'label': row['label'], 'description': row['description'], 'priority': row['priority'],
              'status': row['status'], 'saved_status': status['status'], 'changed_by': status['changed_by']}
             for row in self.todolist_api.get_todolists(todolist_id=todo.todolist_id)
             for status in row['status_changes']],
            [
                {'label': 'List 7', 'description': 'This is List 7', 'priority': 'medium', 'status': 'active',
                 'saved_status': 'active', 'changed_by': 'Test User 1'},
            ]
        )

        self.todolist_api.update_todolist(todo.todolist_id, {'priority': 'a'})
        self.assertEqual(
            [{'label': row['label'], 'description': row['description'], 'priority': row['priority'],
              'status': row['status'], 'saved_status': status['status'], 'changed_by': status['changed_by']}
             for row in self.todolist_api.get_todolists(todolist_id=todo.todolist_id)
             for status in row['status_changes']],
            [
                {'label': 'List 7', 'description': 'This is List 7', 'priority': 'veryhigh', 'status': 'active',
                 'saved_status': 'active', 'changed_by': 'Test User 1'},
            ]
        )

        self.todolist_api.update_todolist(todo.todolist_id, {'status': 'inactive'})
        self.assertEqual(
            [{'label': row['label'], 'description': row['description'], 'priority': row['priority'],
              'status': row['status'], 'saved_status': status['status'], 'changed_by': status['changed_by']}
             for row in self.todolist_api.get_todolists(todolist_id=todo.todolist_id)
             for status in row['status_changes']],
            [
                {'label': 'List 7', 'description': 'This is List 7', 'priority': 'veryhigh', 'status': 'inactive',
                 'saved_status': 'inactive', 'changed_by': 'Test User 1'},
                {'label': 'List 7', 'description': 'This is List 7', 'priority': 'veryhigh', 'status': 'inactive',
                 'saved_status': 'active', 'changed_by': 'Test User 1'},
            ]
        )

    def test_delete_todo_lists(self):
        self.create_todolist_set()

        todo = db.session.query(TodoListTbl).filter_by(label='List 3').first()

        self.assertEqual(
            [{'label': row['label'], 'description': row['description'], 'priority': row['priority'],
              'status': row['status'], 'saved_status': status['status'], 'changed_by': status['changed_by']}
             for row in self.todolist_api.get_todolists(todolist_id=todo.todolist_id)
             for status in row['status_changes']],
            [
                {'label': 'List 3', 'description': None, 'priority': 'medium', 'status': 'active',
                 'saved_status': 'active', 'changed_by': 'Test User 1'},
            ]
        )

        self.assertEqual(self.todolist_api.delete_todolist(todo.todolist_id), True)
        self.assertEqual(list(self.todolist_api.get_todolists(todolist_id=todo.todolist_id)), [])

    def test_permissions_todo_lists(self):
        self.create_todolist_set()

        user2 = UserTbl(user_id=str(uuid4()), login='user2', password='abc123', name='Test User 2',
                        email='user2@example.com', created=datetime.utcnow())
        db.session.add(user2)
        user3 = UserTbl(user_id=str(uuid4()), login='user3', password='abc123', name='Test User 3',
                        email='user3@example.com', created=datetime.utcnow())
        db.session.add(user3)
        db.session.commit()

        todo = db.session.query(TodoListTbl).filter_by(label='List 3').first()

        self.assertEqual(
            [{'login': row['login'], 'role': row['role']} for row in todo.all_roles],
            [{'login': 'user1', 'role': 'owner'}]
        )

        self.assertEqual(self.todolist_api.permissions(todo.todolist_id, self.user.user_id), None)

        # add permissions for user2 and user3
        self.todolist_api.permissions(todo.todolist_id, user2.user_id, 'admin')
        self.todolist_api.permissions(todo.todolist_id, user3.user_id, 'reader')

        self.assertEqual(
            [{'login': row['login'], 'role': row['role']} for row in todo.all_roles],
            [{'login': 'user1', 'role': 'owner'},
             {'login': 'user2', 'role': 'admin'},
             {'login': 'user3', 'role': 'reader'}]
        )

        # remove permission for user 2
        self.todolist_api.permissions(todo.todolist_id, user2.user_id)
        self.assertEqual(
            [{'login': row['login'], 'role': row['role']} for row in todo.all_roles],
            [{'login': 'user1', 'role': 'owner'},
             {'login': 'user3', 'role': 'reader'}]
        )

        # changed owner from user1 to user 3
        self.todolist_api.permissions(todo.todolist_id, user3.user_id, 'owner')
        self.assertEqual(
            [{'login': row['login'], 'role': row['role']} for row in todo.all_roles],
            [{'login': 'user3', 'role': 'owner'}]
        )

        # changed owner from user3 to user 1 and set the previous owner role to reader
        todolist_api_user3 = TodoListApi(user3.user_id)
        todolist_api_user3.permissions(todo.todolist_id, self.user.user_id, 'owner', 'reader')
        self.assertEqual(
            [{'login': row['login'], 'role': row['role']} for row in todo.all_roles],
            [{'login': 'user1', 'role': 'owner'},
             {'login': 'user3', 'role': 'reader'}]
        )
