# todos
Todos flask app with swagger

The repository includes flask app with authorization which
allowes to create todo list.

## Virtual environment

To start using this app create and activate virtual 
environment and install required packages

```sh
$ pyenv local 3.7.2
$ python -mvenv env
$ source env/bin/activate

$ pip install -e ".[dev]"
```

## Run application and use swagger api :)

You will need running mysql server with created db and 
credentials as in config.ini file

In main directory of repository...

Next you will have to run migration:
```sh
$ manage db upgrade
```

```sh
$ FLASK_ENV=development FLASK_APP=todos/app.py flask run
```

Now you can access swagger api in brower:
http://127.0.0.1:5000/api/

The flow is the following:
* Create a user by endpoint user: POST
* Log in by endpoint login: POST
* Now you are able to use GET, PATCH, DELETE from endpoint user
* At the end you can log out by endpoint logout: GET

