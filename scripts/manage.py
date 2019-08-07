import click
from todos import Todos, db
from flask.cli import FlaskGroup, with_appcontext

from todos.config import get_config
import re
import subprocess
import sys


@click.group(cls=FlaskGroup, create_app=lambda _: Todos().app)
def main():
    """Management script."""
    pass


@click.confirmation_option(help='Confirm the action.',
                           prompt='Are you sure you want to clear content of all db tables?')
@main.command(help='Clear content of db tables.')
@with_appcontext
def cleardb():
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()
    print('Database cleared.')


@main.command(help='Open database connection shell.')
def connect():
    try:
        config = get_config()
        for key, value in config.config.items('alembic'):
            if key.upper() == 'SQLALCHEMY_DATABASE_URI':
                url = value
                break
        m = re.match(r"^(?:mysql:\/\/)(\w+):(.+)@([\w-]+)/(\w+)\?(?:.+$)", url)
        subprocess.run([f"MYSQL_PWD={m.groups()[1]} mysql -u{m.groups()[0]} -h{m.groups()[2]} {m.groups()[3]}"],
                       shell=True)
    except Exception as e:
        click.echo(e)
        sys.exit(1)

    return
