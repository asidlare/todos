from marshmallow import Schema, fields


class UserGet(Schema):
    login = fields.Str(required=True)
    user_id = fields.UUID(required=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    created = fields.DateTime(required=True)


class UserPost(Schema):
    login = fields.Str(required=True)
    password = fields.Str(required=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)


class UserPatch(Schema):
    password = fields.Str(required=False)
    name = fields.Str(required=False)
    email = fields.Email(required=False)


class UserError(Schema):
    error = fields.Field(required=True)


class UserOK(Schema):
    response = fields.Field(required=True)


class UserLogin(Schema):
    login = fields.Str(required=True)
    password = fields.Str(required=True)
