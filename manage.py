#! /usr/bin/env python
# -*- coding: utf-8 -*-

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import sys

from app import http_app

manager = Manager(http_app.web_app)


def register_migrate(manager):
    from app import models
    migrate = Migrate(http_app.web_app, models.db)
    manager.add_command('db', MigrateCommand)
    return migrate


if __name__ == '__main__':
    if 'db' in sys.argv:
        migrate = register_migrate(manager)
    manager.run()
