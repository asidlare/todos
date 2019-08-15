# todos
Todos flask app with swagger

The repository includes flask app with authorization which
allowes to create todolists with tasks inside.

## Installation and virtual environment

### Install pyenv
```sh
$ curl https://pyenv.run | bash
```

### Update .bash_profile to load pyenv automatically
```sh
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bash_profile
echo 'eval "$(pyenv init -)"' >> ~/.bash_profile
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bash_profile
```

### Install any python version, eg.:
```sh
$ pyenv install 3.7.2
```

### Create virtual environment
```sh
$ pyenv local 3.7.2
$ python -mvenv env
$ source env/bin/activate

$ pip install -e ".[dev]"
```

## Run application and use swagger api :)

You will need running mysql server with created db and 
credentials as in config.ini file

### Run migration:
```sh
$ manage db upgrade
```

### run gunicorn

```sh
$ ./run_app.sh
```

Now you can access swagger api in brower:
http://127.0.0.1:5000/api/

# Endpoints

The following endpoints are available:
* user for managing users
* login to log into app
* logout
* todolist to manage todolists
* task to manage tasks inside todolists

Below you can see compressed endpoints view:
![compressed endpoints view](doc/todos_endpoints_Swagger_UI.png)

and expanded endpoints view:
![expanded endpoints view](doc/todos_endpoints_expanded_Swagger_UI.png)

Database schema:
[db schema](todos/models/doc/todos.pdf)

# Test coverage

Below you can find test coverage report for the project:
![tests coverage report](doc/todos_tests_coverage_report.png)