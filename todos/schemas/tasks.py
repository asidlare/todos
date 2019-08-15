from marshmallow import Schema, fields
from marshmallow_enum import EnumField
from todos.models.definitions import TaskStatus, Priority


class TaskStatusChanges(Schema):
    change_ts = fields.DateTime(required=True)
    changed_by = fields.Str(required=True)
    status = fields.Str(required=True)


class TaskGet(Schema):
    task_id = fields.UUID(required=True)
    parent_id = fields.UUID(required=True)
    label = fields.Str(required=True)
    description = fields.Str(required=False)
    status = fields.Str(required=True)
    priority = fields.Str(required=True)
    depth = fields.Int(required=True)
    is_leaf = fields.Bool(required=True)
    created_ts = fields.DateTime(required=True)
    todolist_id = fields.UUID(required=True)
    status_changes = fields.Nested(TaskStatusChanges, many=True, required=True)


class TaskPost(Schema):
    parent_id = fields.UUID(required=False, allow_none=True)
    label = fields.Str(required=True)
    description = fields.Str(required=False, allow_none=True)
    status = EnumField(TaskStatus, required=True, dump_by=EnumField.NAME, load_by=EnumField.NAME,
                       missing=TaskStatus.active.name)
    priority = EnumField(Priority, required=True, dump_by=EnumField.VALUE, load_by=EnumField.NAME)


class TaskPatch(Schema):
    label = fields.Str(required=False)
    description = fields.Str(required=False)
    status = EnumField(TaskStatus, required=False, dump_by=EnumField.NAME, load_by=EnumField.NAME)
    priority = EnumField(Priority, required=False, dump_by=EnumField.VALUE, load_by=EnumField.NAME)


class TaskError(Schema):
    error = fields.Field(required=True)


class TaskOK(Schema):
    response = fields.Field(required=True)
