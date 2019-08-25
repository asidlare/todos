from uuid import uuid4
from datetime import datetime
from tests.base import TestCaseWithDB
from todos.models.definitions import (db, UserTbl, RoleTbl, Priority, TodoListStatus,
                                      TaskTbl, TaskStatus)
from todos.models.api.todolists_api import TodoListApi
from todos.models.api.tasks_api import TaskApi


class TaskApiTests(TestCaseWithDB):

    def setUp(self):
        super().setUp()

        self.user = UserTbl(user_id=str(uuid4()), login='user1', password='abc123', name='Test User 1',
                            email='user1@example.com', created=datetime.utcnow())
        db.session.add(self.user)
        db.session.commit()
        owner = RoleTbl(role='owner', change_owner=1, delete=1, change_permissions=1, change_data=1, read=1,
                        todolist_count_limit=10, task_count_limit=100, task_depth_limit=10)
        admin = RoleTbl(role='admin', change_owner=0, delete=0, change_permissions=0, change_data=1, read=1,
                        task_count_limit=80, task_depth_limit=8)
        reader = RoleTbl(role='reader', change_owner=0, delete=0, change_permissions=0, change_data=0, read=1)
        db.session.add(owner)
        db.session.add(admin)
        db.session.add(reader)
        db.session.commit()

        todolist_api = TodoListApi(self.user.user_id)
        self.todolist = todolist_api.create_todolist({'label': 'List 1', 'status': TodoListStatus.active.name,
                                                      'priority': Priority.high.value})

        self.task_api = TaskApi(self.user.user_id, self.todolist.todolist_id)

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
        task0 = self.task_api.create_task({'label': 'Task 0', 'status': 'active', 'priority': Priority.high.value,
                                           'parent_id': None})
        task1 = self.task_api.create_task({'label': 'Task 1', 'status': 'active', 'priority': Priority.medium.value,
                                           'parent_id': task0.task_id})
        task2 = self.task_api.create_task({'label': 'Task 2', 'status': 'done', 'priority': Priority.veryhigh.value,
                                           'parent_id': None})
        task3 = self.task_api.create_task({'label': 'Task 3', 'status': 'done', 'priority': Priority.high.value,
                                           'parent_id': task1.task_id})
        task4 = self.task_api.create_task({'label': 'Task 4', 'status': 'active', 'priority': Priority.medium.value,
                                           'parent_id': task1.task_id})
        self.task_api.create_task({'label': 'Task 5', 'status': 'active', 'priority': Priority.medium.value,
                                   'parent_id': task1.task_id})
        self.task_api.create_task({'label': 'Task 6', 'status': 'active', 'priority': Priority.high.value,
                                   'parent_id': task0.task_id})
        self.task_api.create_task({'label': 'Task 7', 'status': 'done', 'priority': Priority.medium.value,
                                   'parent_id': task2.task_id})
        self.task_api.create_task({'label': 'Task 8', 'status': 'done', 'priority': Priority.medium.value,
                                   'parent_id': task3.task_id})
        self.task_api.create_task({'label': 'Task 9', 'status': 'active', 'priority': Priority.medium.value,
                                   'parent_id': task4.task_id})

    def test_create_task(self):
        task1 = self.task_api.create_task({'label': 'Task1', 'status': TaskStatus.active.name,
                                           'priority': Priority.medium.value})
        self.task_api.create_task({'label': 'Task2', 'status': TaskStatus.active.name,
                                   'priority': Priority.high.value, 'parent_id': task1.task_id})

        self.assertEqual(
            [(row['label'], row['priority'], row['status'], row['depth']) for row in task1.dfs_tree],
            [('Task1', 'medium', 'active', 0), ('Task2', 'high', 'active', 1)]
        )

        self.assertEqual(
            [(change['changed_by'], change['status'])for change in task1.status_changes],
            [('Test User 1', 'active')]
        )

        task1_fetched = self.task_api.read_task_by_id(task1.task_id)

        self.assertEqual(task1, task1_fetched)

        # database error
        self.assertEqual(self.task_api.create_task({'label': 'Task2', 'status': 'read',
                                                    'priority': Priority.high.value, 'parent_id': task1.task_id}),
                         None)

    def test_get_tasks(self):
        self.create_tasks_set()

        # tree from dfs algorithm
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=True)],
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

        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=False)],
            [
                {'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
            ]
        )

        task = db.session.query(TaskTbl).filter_by(label='Task 0').first()
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=True, task_id=task.task_id)],
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

        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=False, task_id=task.task_id)],
            [
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
            ]
        )

    def test_update_task(self):
        self.create_tasks_set()

        task = db.session.query(TaskTbl).filter_by(label='Task 1').first()

        # try to update Task 1 status to done what is impossible because some of its descendants are active now
        self.assertEqual(self.task_api.update_task(task.task_id, {'status': 'done'}), False)

        # update all not done descendants to done
        for label in ('Task 9', 'Task 4', 'Task 5'):
            taskdesc = db.session.query(TaskTbl).filter_by(label=label).first()
            self.assertEqual(self.task_api.update_task(taskdesc.task_id, {'status': 'done'}), True)

        # actually all descendants are done, so try to update again
        self.assertEqual(self.task_api.update_task(task.task_id, {'status': 'done'}), True)

        # before update
        self.assertEqual(
            (task.label, task.description, task.priority.name, task.status.name, task.depth),
            ('Task 1', None, 'medium', 'done', 1)
        )

        # update the rest of updatable fields
        self.assertEqual(self.task_api.update_task(task.task_id, {'status': 'ready', 'label': 'Task 1 ready',
                                                                  'description': 'The task is now ready',
                                                                  'priority': Priority.low.value}), True)

        # after update
        self.assertEqual(
            (task.label, task.description, task.priority.name, task.status.name, task.depth),
            ('Task 1 ready', 'The task is now ready', 'low', 'ready', 1)
        )

        # change with db error
        self.assertEqual(self.task_api.update_task(task.task_id, {'status': 'read'}), None)

    def test_delete_task(self):
        self.create_tasks_set()

        task = db.session.query(TaskTbl).filter_by(label='Task 1').first()

        # tree before deleting
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=True)],
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

        self.assertEqual(self.task_api.delete_task(task.task_id), True)

        # tree after deleting
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=True)],
            [
                {'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 7', 'priority': 'medium', 'status': 'done', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
            ]
        )

    def test_purge(self):
        self.create_tasks_set()

        db.session.query(TaskTbl).filter_by(label='Task 1').first()

        # tree before purging
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=True)],
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

        self.assertEqual(self.task_api.purge_tasks(), True)

        # tree after purging
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=True)],
            [
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 1, 'is_leaf': False},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': True}
            ]
        )

    def test_checking_if_it_is_possible_to_reparent(self):
        self.create_tasks_set()

        task0 = db.session.query(TaskTbl).filter_by(label='Task 0').first()
        task1 = db.session.query(TaskTbl).filter_by(label='Task 1').first()
        task2 = db.session.query(TaskTbl).filter_by(label='Task 2').first()

        self.assertEqual(self.task_api._it_is_possible_to_reparent(task1.task_id, task1.task_id),
                         False, 'task itself cannot be parent')
        self.assertEqual(self.task_api._it_is_possible_to_reparent('123', task1.task_id),
                         False, 'task not exists')
        self.assertEqual(self.task_api._it_is_possible_to_reparent(None, task1.task_id),
                         False, 'task cannot be none')
        self.assertEqual(self.task_api._it_is_possible_to_reparent(task1.task_id, '123'),
                         False, 'parent not exists')
        self.assertEqual(self.task_api._it_is_possible_to_reparent(task0.task_id, None),
                         False, 'the same parent none')
        self.assertEqual(self.task_api._it_is_possible_to_reparent(task1.task_id, None),
                         True, 'different parent none - ok')
        self.assertEqual(self.task_api._it_is_possible_to_reparent(task1.task_id, task2.task_id),
                         True, 'different parent not none - ok')
        self.assertEqual(self.task_api._it_is_possible_to_reparent(task0.task_id, task1.task_id),
                         False, 'task cannot be moved to its descendant')

    def test_reparent(self):
        self.create_tasks_set()

        task1 = db.session.query(TaskTbl).filter_by(label='Task 1').first()
        task7 = db.session.query(TaskTbl).filter_by(label='Task 7').first()

        # initial tree
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=True)],
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
        self.assertEqual(self.task_api.reparent_tasks(task1.task_id, task1.task_id), False)

        # nothing changed, bad parent
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=True)],
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

        # nothing changed, good parent but depth limit exceeded
        db.session.query(RoleTbl).filter_by(role='owner').update({'task_depth_limit': 3})
        db.session.commit()
        self.assertEqual(self.task_api.reparent_tasks(task1.task_id, task7.task_id), False)

        # nothing changed, good parent but depth limit exeeded
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=True)],
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

        # changed
        db.session.query(RoleTbl).filter_by(role='owner').update({'task_depth_limit': 10})
        db.session.commit()
        self.assertEqual(self.task_api.reparent_tasks(task1.task_id, task7.task_id), True)

        # changed
        self.assertEqual(
            [{'label': row['label'], 'priority': row['priority'], 'status': row['status'], 'depth': row['depth'],
              'is_leaf': row['is_leaf']} for row in self.task_api.get_tasks(expand=True)],
            [
                {'label': 'Task 2', 'priority': 'veryhigh', 'status': 'done', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 7', 'priority': 'medium', 'status': 'done', 'depth': 1, 'is_leaf': False},
                {'label': 'Task 1', 'priority': 'medium', 'status': 'active', 'depth': 2, 'is_leaf': False},
                {'label': 'Task 3', 'priority': 'high', 'status': 'done', 'depth': 3, 'is_leaf': False},
                {'label': 'Task 8', 'priority': 'medium', 'status': 'done', 'depth': 4, 'is_leaf': True},
                {'label': 'Task 4', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': False},
                {'label': 'Task 9', 'priority': 'medium', 'status': 'active', 'depth': 4, 'is_leaf': True},
                {'label': 'Task 5', 'priority': 'medium', 'status': 'active', 'depth': 3, 'is_leaf': True},
                {'label': 'Task 0', 'priority': 'high', 'status': 'active', 'depth': 0, 'is_leaf': False},
                {'label': 'Task 6', 'priority': 'high', 'status': 'active', 'depth': 1, 'is_leaf': True}
            ]
        )
