from marshmallow import Schema, fields
from marshmallow_enum import EnumField
from todos.models.definitions import TodoListStatus, Priority


class TodoListID(Schema):
    todolist_id = fields.UUID(required=False)


class TodoListLabel(Schema):
    label = fields.String(required=False)


class TodoListStatusField(Schema):
    status = EnumField(TodoListStatus, required=False, dump_by=EnumField.NAME, load_by=EnumField.NAME)


class TodoListPriorityField(Schema):
    priority = EnumField(Priority, required=False, dump_by=EnumField.VALUE, load_by=EnumField.NAME)


class TodoListStatusChanges(Schema):
    change_ts = fields.DateTime(required=True)
    changed_by = fields.Str(required=True)
    status = fields.Str(required=True)


class TodoListGet(Schema):
    todolist_id = fields.UUID(required=True)
    label = fields.Str(required=True)
    description = fields.Str(required=False)
    status = fields.Str(required=True)
    priority = fields.Str(required=True)
    created_ts = fields.DateTime(required=True)
    status_changes = fields.Nested(TodoListStatusChanges, many=True, required=True)


class TodoListPost(Schema):
    label = fields.Str(required=True)
    description = fields.Str(required=False)
    status = EnumField(TodoListStatus, required=False, dump_by=EnumField.NAME, load_by=EnumField.NAME,
                       missing=TodoListStatus.active.name)
    priority = EnumField(Priority, required=True, dump_by=EnumField.VALUE, load_by=EnumField.NAME)


class TodoListPatch(Schema):
    label = fields.Str(required=False)
    description = fields.Str(required=False)
    status = EnumField(TodoListStatus, required=False, dump_by=EnumField.NAME, load_by=EnumField.NAME)
    priority = EnumField(Priority, required=False, dump_by=EnumField.VALUE, load_by=EnumField.NAME)


class TodoListError(Schema):
    error = fields.Field(required=True)


class TodoListOK(Schema):
    response = fields.Field(required=True)
