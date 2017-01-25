web: gunicorn app.http_app:web_app --log-file -
worker: celery worker --app=app.worker.wat_worker --beat