#  -*- coding: utf-8 -*-

import os
from importlib import import_module


class Config(object):
    DEBUG = False
    TESTING = False
    DEVELOPMENT = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    AUTH_KEY = os.environ['AUTH_KEY']


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    KEY_ON_TEST = 'KEY ON TEST'


class ConfigClassNotFound(Exception):
    """
    Raises when the APP_SETTINGS environment variable have a value which does not point to an uninstantiable class.
    """
    pass


def get_config():
    """
    Get the Config Class instance defined in APP_SETTINGS environment variable
    :return The config class instance
    :rtype: Config
    """
    config_imports = os.environ['APP_SETTINGS'].split('.')
    config_class_name = config_imports[-1]
    config_module = import_module('.'.join(config_imports[:-1]))
    config_class = getattr(config_module, config_class_name, None)
    if not config_class:
        raise ConfigClassNotFound('Unable to find a config class in {}'.format(os.environ['APP_SETTINGS']))
    return config_class()