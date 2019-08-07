import os
import logging
import logging.config
from configparser import ConfigParser, ExtendedInterpolation

logger = logging.getLogger('todos')

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class DefaultConfig:
    def __init__(self):
        self.config = ConfigParser(interpolation=ExtendedInterpolation())
        self.config.set("DEFAULT", "root_path", root_path)

        self.read_config()

        self.set_attrs_from_config()

        logger.debug(f"[DefaultConfig] Config loaded: {self.__dict__}")

    def read_config(self):
        logger.debug(f"[DefaultConfig] Loading config, root: {root_path}")
        self.config.read([f"{root_path}/config.ini"])

    def set_attrs_from_config(self):
        for key, val in self.config.items('todos'):
            logger.debug(f"[DefaultConfig] Setting attr {key} to {val}")
            setattr(self, key.upper(), val)


class TestingConfig(DefaultConfig):
    def read_config(self):
        logger.debug(f"[TestingConfig] Loading test config, root: {root_path}")
        # This will overwrite stuff from config.ini with that in testing ini,
        # provided sections match.
        self.config.read([f"{root_path}/config.ini", f"{root_path}/testing.ini"])


def get_config(config=DefaultConfig(), testing_config=TestingConfig()):
    is_testing = os.environ.get('TEST', False)
    logger.debug(f"[get_config] Is testing env: {is_testing}")
    return config if not is_testing else testing_config


def setup_logging():
    """Load logging configuration"""
    is_testing = os.environ.get('TEST', False)
    config_file = 'config.ini' if not is_testing else 'testing.ini'
    logger.debug(f"[setup_logging] Is testing env: {is_testing},"
                 f' loading config file {config_file}')
    logging.config.fileConfig(f"{root_path}/{config_file}")
