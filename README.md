
# Wat Shou Da Pay

## Development Environment

### Install Python PIPY:

    $ sudo easy_install pip

### Install virtualenvwrapper:

    $ sudo pip install --ignore-installed virtualenvwrapper

Add these lines to your `.bashrc` file:

    export WORKON_HOME=$HOME/.virtualenvs
    export PROJECT_HOME=$HOME/projects
    source /usr/local/bin/virtualenvwrapper.sh

Open a terminal window and source ~/.bashrc
    $ source ~/.bashrc

Open a terminal window and create the virtualenv:

    $ mkvirtualenv watshodapay

Add enviroment variables to postactivate:

    $ vim $WORKON_HOME/watshodapay/bin/postactivate

Update this file with:

    export APP_SETTINGS=app.config.DevelopmentConfig
    export SECRET_KEY=SECCRETEEETTTTTTT
    export APP_SETTINGS=app.config.DevelopmentConfig
    export SECRET_KEY=SECCRETEEETTTTTTT
    export DATABASE_URL=postgresql+psycopg2://watshodapay:watshodapay@localhost:5432/watshodapay
    export AUTH_KEY=ZASZESZISZOSZUS

To activate the virtualenv:

    $ workon watshodapay

Install dependencies in virtualenv:

    $ pip install -r requirements.txt
    $ pip install -r requirements_dev.txt

To create the DATABASE:

    * Note: You'll need to have a local database for your user to this command work

    $ psql
    $ CREATE DATABASE watshodapay;
    $ CREATE ROLE watshodapay SUPERUSER LOGIN PASSWORD 'watshodapay';
    $ ALTER DATABASE watshodapay OWNER TO watshodapay;

To generate DB migrations:

    $ python manage.py db migrate

To run migration in DB

    $ python manage.py db upgrade

To run the HTTP App:

    $ python run.py
