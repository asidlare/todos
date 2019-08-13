from uuid import uuid4
from datetime import datetime
from tests.base import TestCaseWithDB
from todos.models.definitions import (db, UserTbl, TodoListTbl, TodoListCreatorTbl, UserTodoListTbl, RoleTbl,
                                      Priority, TaskTbl)


class SimpleDefTests(TestCaseWithDB):

    def setUp(self):
        super().setUp()

        self.user1 = UserTbl(user_id=str(uuid4()), login='user1', password='abc123', name='Test User 1',
                             email='user1@example.com', created=datetime.utcnow())
        db.session.add(self.user1)
        self.user2 = UserTbl(user_id=str(uuid4()), login='user2', password='abc123', name='Test User 2',
                             email='user2@example.com', created=datetime.utcnow())
        db.session.add(self.user2)
        self.user3 = UserTbl(user_id=str(uuid4()), login='user3', password='abc123', name='Test User 2',
                             email='user3@example.com', created=datetime.utcnow())
        db.session.add(self.user3)
        db.session.commit()
        owner = RoleTbl(role='owner', change_owner=1, delete=1, change_permissions=1, change_data=1, read=1)
        admin = RoleTbl(role='admin', change_owner=0, delete=0, change_permissions=0, change_data=1, read=1)
        reader = RoleTbl(role='reader', change_owner=0, delete=0, change_permissions=0, change_data=0, read=1)
        db.session.add(owner)
        db.session.add(admin)
        db.session.add(reader)
        db.session.commit()

    def test_add_todo_list(self):
        todo = TodoListTbl(todolist_id=str(uuid4()), label='List 1', status='active', priority=Priority.medium.value,
                           created_ts=datetime.utcnow())
        db.session.add(todo)
        creator = TodoListCreatorTbl(TodoList=todo, User=self.user1)
        db.session.add(creator)
        assoc1 = UserTodoListTbl(User=self.user1, TodoList=todo, role='owner')
        assoc2 = UserTodoListTbl(User=self.user2, TodoList=todo, role='reader')
        db.session.add(assoc1)
        db.session.add(assoc2)
        db.session.commit()

        # check creator
        self.assertEqual(todo.creator, self.user1.user_id)

        # check user1 role
        self.assertEqual(todo.role(self.user1.user_id), 'owner')

        # check user2 role
        self.assertEqual(todo.role(self.user2.user_id), 'reader')

        # check user3 role
        self.assertEqual(todo.role(self.user3.user_id), None)

        # check users for todolist
        self.assertEqual(
            todo.all_roles,
            [{'login': 'user1', 'name': 'Test User 1', 'email': 'user1@example.com', 'role': 'owner'},
             {'login': 'user2', 'name': 'Test User 2', 'email': 'user2@example.com', 'role': 'reader'}]
        )

        # check user roles
        self.assertEqual(self.user1.role(todo.todolist_id), 'owner')
        self.assertEqual(self.user2.role(todo.todolist_id), 'reader')

    def test_add_todo_lists(self):
        todolists = list()
        todolists.append(TodoListTbl(todolist_id=str(uuid4()), label='List 1', status='active',
                                     priority=Priority.high.value, created_ts=datetime.utcnow()))
        todolists.append(TodoListTbl(todolist_id=str(uuid4()), label='List 2', status='inactive',
                                     priority=Priority.medium.value, created_ts=datetime.utcnow()))
        todolists.append(TodoListTbl(todolist_id=str(uuid4()), label='List 4', status='active',
                                     priority=Priority.medium.value, created_ts=datetime.utcnow()))
        todolists.append(TodoListTbl(todolist_id=str(uuid4()), label='List 3', status='active',
                                     priority=Priority.medium.value, created_ts=datetime.utcnow()))
        todolists.append(TodoListTbl(todolist_id=str(uuid4()), label='List 5', status='inactive',
                                     priority=Priority.veryhigh.value, created_ts=datetime.utcnow()))
        todolists.append(TodoListTbl(todolist_id=str(uuid4()), label='List 6', status='active',
                                     priority=Priority.veryhigh.value, created_ts=datetime.utcnow()))
        for todo in todolists:
            db.session.add(todo)
            db.session.add(TodoListCreatorTbl(TodoList=todo, User=self.user1))
            db.session.add(UserTodoListTbl(User=self.user1, TodoList=todo, role='owner'))
        db.session.commit()

        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in self.user1.all_todolists()],
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
             for row in self.user1.all_todolists(priority='medium')],
            [
                {'label': 'List 3', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 4', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 2', 'priority': 'medium', 'status': 'inactive'}
            ]
        )

        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in self.user1.all_todolists(priority='medium', status='active')],
            [
                {'label': 'List 3', 'priority': 'medium', 'status': 'active'},
                {'label': 'List 4', 'priority': 'medium', 'status': 'active'},
            ]
        )

        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in self.user1.all_todolists(priority='medium', status='active', label='List 4')],
            [
                {'label': 'List 4', 'priority': 'medium', 'status': 'active'},
            ]
        )

    def test_add_tasks(self):
        # add todolist
        todo = TodoListTbl(todolist_id=str(uuid4()), label='List 1', status='active', priority=Priority.medium.value,
                           created_ts=datetime.utcnow())
        db.session.add(todo)
        creator = TodoListCreatorTbl(TodoList=todo, User=self.user1)
        db.session.add(creator)
        assoc1 = UserTodoListTbl(User=self.user1, TodoList=todo, role='owner')
        db.session.add(assoc1)
        db.session.commit()
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
        ids = [str(uuid4()) for x in range(10)]
        labels = [f"Task {x}" for x in range(10)]
        parents = [None, ids[0], None, ids[1], ids[1], ids[1], ids[0], ids[2], ids[3], ids[4]]
        priorities = [Priority.high.value, Priority.medium.value, Priority.veryhigh.value, Priority.high.value,
                      Priority.medium.value, Priority.medium.value, Priority.high.value, Priority.medium.value,
                      Priority.medium.value, Priority.medium.value]
        statuses = ['active', 'active', 'done', 'done', 'active', 'active', 'active', 'done', 'done', 'active']
        tasks = list()
        for task_id, label, parent_id, priority, status in zip(ids, labels, parents, priorities, statuses):
            task = TaskTbl(task_id=task_id, label=label, parent_id=parent_id, priority=priority, status=status,
                           TodoList=todo, created_ts=datetime.utcnow())
            tasks.append(task)
            db.session.add(task)
        db.session.commit()

        # check children
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status']}
             for row in tasks[0].children],
            [{'label': 'Task 6', 'priority': 'high', 'status': 'active'},
             {'label': 'Task 1', 'priority': 'medium', 'status': 'active'}]
        )

        # siblings
        # task with no parent (belongs to particular todolist
        self.assertEqual(
            [{'label': row.label, 'priority': row.priority.name, 'status': row.status.name}
             for row in tasks[0].siblings],
            [{'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done'},
             {'label': 'Task 0', 'priority': 'high', 'status': 'active'}]
        )
        # task with parent
        self.assertEqual(
            [{'label': row.label, 'priority': row.priority.name, 'status': row.status.name}
             for row in tasks[3].siblings],
            [{'label': 'Task 3', 'priority': 'high', 'status': 'done'},
             {'label': 'Task 4', 'priority': 'medium', 'status': 'active'},
             {'label': 'Task 5', 'priority': 'medium', 'status': 'active'}]
        )

        # tree from dfs algorithm
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in tasks[0].dfs_tree],
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

        # tree from dfs algorithm
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in tasks[1].dfs_tree],
            [
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
                {'label': 'Task 3', 'priority': 'high', 'status': 'done', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 8', 'priority': 'medium', 'status': 'done', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': True}
            ]
        )

        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in tasks[1].descendants],
            [
                {'label': 'Task 3', 'priority': 'high', 'status': 'done', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 8', 'priority': 'medium', 'status': 'done', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': True}
            ]
        )

        self.assertEqual(
            tuple(tasks[4].ancestors),
            (tasks[1].task_id, tasks[0].task_id)
        )

    def test_more_todolists_with_tasks(self):
        # add first todolist
        todo1 = TodoListTbl(todolist_id=str(uuid4()), label='List 1', status='active', priority=Priority.medium.value,
                            created_ts=datetime.utcnow())
        db.session.add(todo1)
        creator = TodoListCreatorTbl(TodoList=todo1, User=self.user1)
        db.session.add(creator)
        assoc1 = UserTodoListTbl(User=self.user1, TodoList=todo1, role='owner')
        db.session.add(assoc1)
        db.session.commit()

        task11 = TaskTbl(task_id=str(uuid4()), label='Task 11', parent_id=None, priority=Priority.medium,
                         status='active', TodoList=todo1, created_ts=datetime.utcnow())
        db.session.add(task11)
        task12 = TaskTbl(task_id=str(uuid4()), label='Task 12', parent_id=task11.task_id, priority=Priority.medium,
                         status='active', TodoList=todo1, created_ts=datetime.utcnow())
        db.session.add(task12)
        db.session.commit()

        # add second todolist
        todo2 = TodoListTbl(todolist_id=str(uuid4()), label='List 2', status='active', priority=Priority.medium.value,
                            created_ts=datetime.utcnow())
        db.session.add(todo2)
        creator = TodoListCreatorTbl(TodoList=todo2, User=self.user1)
        db.session.add(creator)
        assoc1 = UserTodoListTbl(User=self.user1, TodoList=todo2, role='owner')
        db.session.add(assoc1)
        db.session.commit()

        task21 = TaskTbl(task_id=str(uuid4()), label='Task 21', parent_id=None, priority=Priority.medium,
                         status='active', TodoList=todo2, created_ts=datetime.utcnow())
        db.session.add(task21)
        task22 = TaskTbl(task_id=str(uuid4()), label='Task 22', parent_id=task21.task_id, priority=Priority.medium,
                         status='active', TodoList=todo2, created_ts=datetime.utcnow())
        db.session.add(task22)
        db.session.commit()

        # tree from dfs algorithm
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in task11.dfs_tree],
            [
                {'label': 'Task 11', 'priority': 'medium', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 12', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': True},
            ]
        )
