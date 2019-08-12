from .base import db, DictMixin, DATETIME_TYPE, BOOLEAN_TYPE
from sqlalchemy_utils import PasswordType, EmailType, force_auto_coercion
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum
from flask_login import UserMixin

force_auto_coercion()


class TodoListStatus(Enum):
    active = 1
    inactive = 2


class TaskStatus(Enum):
    active = 1
    done = 2
    ready = 3


class Priority(Enum):
    veryhigh = 'a'
    high = 'b'
    medium = 'c'
    low = 'd'
    verylow = 'e'


class UserTbl(db.Model, UserMixin, DictMixin):
    """
    Table with user details.
    """
    __tablename__ = 'User'

    __str__ = lambda self: str(self.to_dict()) # noqa
    __repr__ = lambda self: repr(self.to_dict()) # noqa

    user_id = db.Column(db.CHAR(36), primary_key=True)
    login = db.Column(db.String(length=80), nullable=False, unique=True)
    password = db.Column(PasswordType(schemes=['pbkdf2_sha512']), nullable=False)
    name = db.Column(db.String(length=255), nullable=False)
    email = db.Column(EmailType, nullable=False, unique=True)
    created = db.Column(DATETIME_TYPE, nullable=False)

    # Many to many relationship user <--> todolist with roles
    # elements of relation are presorted in required order
    todolists = db.relationship('TodoListTbl', lazy='dynamic', secondary='UserTodoList', back_populates='users',
                                order_by=lambda: (TodoListTbl.priority, TodoListTbl.status, TodoListTbl.label,
                                                  TodoListTbl.created_ts))

    # One to many relationship user <--> todolists creator
    todolistcreator = db.relationship('TodoListCreatorTbl', back_populates='User')

    # One to many relationship user <--> todolists statuses
    todoliststatuses = db.relationship('TodoListStatusChangeLogTbl', back_populates='User')

    # One to many relationship user <--> task statuses
    taskstatuses = db.relationship('TaskStatusChangeLogTbl', back_populates='User')

    def get_id(self):
        """Return user_id per login"""
        return self.user_id

    def is_authenticated(self, login, password):
        """Return True if valid credentials provided"""
        if self.login == login and self.password == password:
            return True
        return False

    def role(self, todolist_id):
        role_row = [row.role for row in self.todolists_assoc if row.todolist_id == todolist_id]
        return role_row[0] if role_row else None

    def all_todolists(self, label=None, status=None, priority=None):
        todolists = self.todolists
        if label:
            todolists = todolists.filter_by(label=label)
        if status:
            todolists = todolists.filter_by(status=getattr(TodoListStatus, status).name)
        if priority:
            todolists = todolists.filter_by(priority=getattr(Priority, priority).value)
        return (row.to_dict() for row in todolists
                for user_role in row.users_assoc if user_role.user_id == self.user_id)

    def to_dict(self):
        out = super().to_dict()
        out.pop('password')
        return out


class RoleTbl(db.Model, DictMixin):
    """
    Table with role permissions.
    Expected roles with permissions:
    - owner (change_owner, delete, add_permissions, change, read)
    - administrator (change, read)
    - reader (read)
    """
    __tablename__ = 'Role'

    __str__ = lambda self: str(self.to_dict()) # noqa
    __repr__ = lambda self: repr(self.to_dict()) # noqa

    role = db.Column(db.String(length=50), primary_key=True)
    change_owner = db.Column(BOOLEAN_TYPE, nullable=False)
    delete = db.Column(BOOLEAN_TYPE, nullable=False)
    change_permissions = db.Column(BOOLEAN_TYPE, nullable=False)
    change_data = db.Column(BOOLEAN_TYPE, nullable=False)
    read = db.Column(BOOLEAN_TYPE, nullable=False)


class TodoListTbl(db.Model, DictMixin):
    """
    TodoList table includes roots of lists
    """
    __tablename__ = 'TodoList'

    __str__ = lambda self: str(self.to_dict()) # noqa
    __repr__ = lambda self: repr(self.to_dict()) # noqa

    todolist_id = db.Column(db.CHAR(36), primary_key=True)
    label = db.Column(db.String(length=255), nullable=False)
    description = db.Column(db.String(length=255), nullable=True)
    status = db.Column(db.Enum(TodoListStatus), nullable=False)
    # inserting values into table to guarantee specific ordering by priority
    priority = db.Column(db.Enum(Priority, values_callable=lambda x: [e.value for e in x]), nullable=False)
    created_ts = db.Column(DATETIME_TYPE, nullable=False)

    # Many to many relationship user <--> todolist with roles
    users = db.relationship('UserTbl', secondary='UserTodoList', back_populates='todolists',
                            order_by=lambda: (UserTbl.name))

    # One to many relationship todolist <--> tasks
    tasks = db.relationship('TaskTbl', back_populates='TodoList',
                            order_by=lambda: (TaskTbl.priority, TaskTbl.status, TaskTbl.label, TaskTbl.created_ts))

    # One to many relationship todolist <--> logs
    statuses = db.relationship('TodoListStatusChangeLogTbl', back_populates='TodoList',
                               order_by=lambda: (TodoListStatusChangeLogTbl.change_ts.desc()))

    # One to many relationship todolist <--> statuses
    tasks = db.relationship('TaskTbl', back_populates='TodoList',
                            order_by=lambda: (TaskTbl.priority, TaskTbl.status, TaskTbl.label, TaskTbl.created_ts))

    # One to one relationship todolist <--> todolist ownership
    TodoListCreator = db.relationship("TodoListCreatorTbl", uselist=False, back_populates="TodoList")

    def role(self, user_id):
        role_row = [row.role for row in self.users_assoc if row.user_id == user_id]
        return role_row[0] if role_row else None

    @property
    def all_roles(self):
        return [{'login': row.login, 'name': row.name, 'email': row.email, 'role': user_role.role}
                for row in self.users
                for user_role in row.todolists_assoc if user_role.todolist_id == self.todolist_id]

    @property
    def children_tasks(self):
        return (row for row in self.tasks if row.parent_id is None)

    @property
    def creator(self):
        return self.TodoListCreator.created_by if self.TodoListCreator else None

    @property
    def status_changes(self):
        return [row.to_dict() for row in self.statuses]

    def to_dict(self):
        out = super().to_dict()
        out['status'] = self.status.name
        out['priority'] = self.priority.name
        out['status_changes'] = self.status_changes
        return out


class TodoListStatusChangeLogTbl(db.Model, DictMixin):
    """
    Table to hold status changes for todolist
    """
    __tablename__ = 'TodoListStatusChangeLog'

    __str__ = lambda self: str(self.to_dict()) # noqa
    __repr__ = lambda self: repr(self.to_dict()) # noqa

    todolist_id = db.Column(db.CHAR(36), db.ForeignKey('TodoList.todolist_id', ondelete="cascade"), primary_key=True)
    change_ts = db.Column(DATETIME_TYPE, primary_key=True)
    changed_by = db.Column(db.CHAR(36), db.ForeignKey('User.user_id', ondelete="cascade"), nullable=False)
    status = db.Column(db.Enum(TodoListStatus), nullable=False)

    # many to one todolists statuses <=> users
    User = db.relationship("UserTbl", back_populates="todoliststatuses")

    # many to one todolists statuses <=> todolist
    TodoList = db.relationship("TodoListTbl", back_populates="statuses")

    def to_dict(self):
        out = super().to_dict()
        out.pop('todolist_id')
        out['status'] = self.status.name
        out['changed_by'] = self.User.name
        return out


class TodoListCreatorTbl(db.Model, DictMixin):
    """
    Table to hold connection between todolist and its creator
    """
    __tablename__ = 'TodoListCreator'

    __str__ = lambda self: str(self.to_dict()) # noqa
    __repr__ = lambda self: repr(self.to_dict()) # noqa

    todolist_id = db.Column(db.CHAR(36), db.ForeignKey('TodoList.todolist_id', ondelete="cascade"), primary_key=True)
    created_by = db.Column(db.CHAR(36), db.ForeignKey('User.user_id', ondelete="cascade"), nullable=False)

    # many to one todolists creator <=> users
    User = db.relationship("UserTbl", back_populates="todolistcreator")

    # one to one todolist creator <=> todolist
    TodoList = db.relationship("TodoListTbl", back_populates="TodoListCreator")


class UserTodoListTbl(db.Model, DictMixin):
    """
    Table to hold roles users for lists.
    Only one user can be owner
    """
    __tablename__ = 'UserTodoList'

    __str__ = lambda self: str(self.to_dict()) # noqa
    __repr__ = lambda self: repr(self.to_dict()) # noqa

    user_id = db.Column(db.CHAR(36), db.ForeignKey('User.user_id', ondelete="cascade"), primary_key=True)
    todolist_id = db.Column(db.CHAR(36), db.ForeignKey('TodoList.todolist_id', ondelete="cascade"), primary_key=True)
    role = db.Column(db.String(length=50), db.ForeignKey('Role.role', ondelete="cascade"), nullable=False)

    User = db.relationship(UserTbl, backref=db.backref("todolists_assoc"))
    TodoList = db.relationship(TodoListTbl, backref=db.backref("users_assoc"))


class TaskTbl(db.Model, DictMixin):
    """
    Table to hold detailed information about tasks.
    """
    __tablename__ = 'Task'

    __str__ = lambda self: str(self.to_dict()) # noqa
    __repr__ = lambda self: repr(self.to_dict()) # noqa

    task_id = db.Column(db.CHAR(36), primary_key=True)
    parent_id = db.Column(db.CHAR(36), db.ForeignKey('Task.task_id', ondelete="cascade"), nullable=True)
    label = db.Column(db.String(length=255), nullable=False, index=True)
    description = db.Column(db.Text(), nullable=True)
    todolist_id = db.Column(db.CHAR(36), db.ForeignKey('TodoList.todolist_id', ondelete="cascade"), nullable=False,
                            index=True)
    status = db.Column(db.Enum(TaskStatus), nullable=False)
    # inserting values into table to guarantee specific ordering by priority
    priority = db.Column(db.Enum(Priority, values_callable=lambda x: [e.value for e in x]), nullable=False)
    created_ts = db.Column(DATETIME_TYPE, nullable=False)

    # relation inside table
    children_one_level = db.relationship("TaskTbl", backref=db.backref('parent', remote_side=[task_id]),
                                         order_by=lambda: (TaskTbl.priority, TaskTbl.status, TaskTbl.label,
                                                           TaskTbl.created_ts))

    # many to one todolists task <=> todolist
    TodoList = db.relationship("TodoListTbl", back_populates="tasks")

    # One to many relationship task <--> statuses
    statuses = db.relationship('TaskStatusChangeLogTbl', back_populates='Task',
                               order_by=lambda: (TaskStatusChangeLogTbl.change_ts.desc()))

    @property
    def children(self):
        return (row.to_dict() for row in self.children_one_level)

    @property
    def siblings(self):
        if self.parent_id:
            return (row for row in self.parent.children_one_level)
        else:
            return (row for row in self.TodoList.children_tasks)

    @property
    def ancestors(self):
        task = self
        while task.parent is not None:
            task = task.parent
            yield task.task_id

    @property
    def descentants(self):
        visited = list()
        return (row['task_id'] for row in self.dfs_tree_from_object(visited) if row != self.to_dict())

    @property
    def dfs_tree(self):
        visited = list()

        if self.parent is None:
            for node in self.siblings:
                visited = node.dfs_tree_from_object(visited)
        else:
            visited = self.dfs_tree_from_object(visited)
        return iter(visited)

    def dfs_tree_from_object(self, visited=None):
        current = self
        visited.append(current.to_dict())

        for node in current.children_one_level:
            if node not in visited:
                node.dfs_tree_from_object(visited)
        return visited

    @property
    def is_leaf(self):
        return False if self.children_one_level else True

    @property
    def status_changes(self):
        return [row.to_dict() for row in self.statuses]

    @hybrid_property
    def depth(self):
        return self.parent.depth + 1 if self.parent_id else 0

    def to_dict(self):
        out = super().to_dict()
        out['status'] = self.status.name
        out['priority'] = self.priority.name
        out['depth'] = self.depth
        out['is_leaf'] = self.is_leaf
        out['status_changes']: self.status_changes
        return out


class TaskStatusChangeLogTbl(db.Model, DictMixin):
    """
    Table to hold status changes for task
    """
    __tablename__ = 'TaskStatusChangeLog'

    __str__ = lambda self: str(self.to_dict()) # noqa
    __repr__ = lambda self: repr(self.to_dict()) # noqa

    task_id = db.Column(db.CHAR(36), db.ForeignKey('Task.task_id', ondelete="cascade"), primary_key=True)
    change_ts = db.Column(DATETIME_TYPE, primary_key=True)
    changed_by = db.Column(db.CHAR(36), db.ForeignKey('User.user_id', ondelete="cascade"), nullable=False)
    status = db.Column(db.Enum(TaskStatus), nullable=False)

    # many to one tasks statuses <=> users
    User = db.relationship("UserTbl", back_populates="taskstatuses")

    # many to one todolists statuses <=> task
    Task = db.relationship("TaskTbl", back_populates="statuses")

    def to_dict(self):
        out = super().to_dict()
        out['status'] = self.status.name
        return out
