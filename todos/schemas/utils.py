from marshmallow import Schema
from marshmallow_enum import EnumField
from enum import Enum


class RoleWithOwnerEnum(Enum):
    admin = 1
    reader = 2
    owner = 3


class RoleWithoutOwnerEnum(Enum):
    admin = 1
    reader = 2


class RoleWithOwner(Schema):
    role = EnumField(RoleWithOwnerEnum, required=False, dump_by=EnumField.NAME, load_by=EnumField.NAME)


class RoleWithoutOwner(Schema):
    new_owner_role = EnumField(RoleWithoutOwnerEnum, required=False, dump_by=EnumField.NAME, load_by=EnumField.NAME)
