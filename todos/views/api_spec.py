from flask import Blueprint, jsonify
from apispec import APISpec
from apispec_webframeworks.flask import FlaskPlugin
from apispec.ext.marshmallow import MarshmallowPlugin
from .user import User
from .login import Login
from .logout import Logout

api_spec = Blueprint('api_spec', __name__, url_prefix='/api/v1')


@api_spec.route('/', methods=['GET'])
def get():
    spec = APISpec(
        title="Todos",
        version="0.1.0",
        openapi_version="3.0.2",
        info={"description": "Todos API"},
        plugins=[FlaskPlugin(), MarshmallowPlugin()]
    )

    spec.components.schema("User")
    spec.path(view=User.collection_view)

    spec.components.schema("Login")
    spec.path(view=Login.collection_view)

    spec.components.schema("Logout")
    spec.path(view=Logout.collection_view)

    return jsonify(spec.to_dict())
