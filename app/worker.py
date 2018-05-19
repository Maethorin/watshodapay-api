# -*- coding: utf-8 -*-

# import os
# from datetime import timedelta

# from celery import Celery
# from celery.schedules import crontab

# from app import models


# wat_worker = Celery('watshodapay')
# wat_worker.conf.update(
#     CELERY_TASK_SERIALIZER='json',
#     CELERY_ACCEPT_CONTENT=['json'],
#     CELERY_RESULT_SERIALIZER='json',
#     CELERY_TIMEZONE='America/Sao_Paulo',
#     BROKER_URL=os.environ['REDIS_URL'],
#     CELERY_RESULT_BACKEND=os.environ['REDIS_URL'],
    # CELERYBEAT_SCHEDULE={
    #     'check_expiring_debt': {
    #         'task': 'wat_worker.check_expiring_debt',
    #         'schedule': timedelta(hours=5)
    #     },
    #     'reset_payed_status': {
    #         'task': 'wat_worker.reset_payed_status',
    #         'schedule': crontab(minute=1, hour=0, day_of_month='1')
    #     }
    # }
# )


# @wat_worker.task(name='wat_worker.check_expiring_debt')
# def check_expiring_debt():
#     print 'STARTING'
#     print 'FINISHED'


# @wat_worker.task(name='wat_worker.reset_payed_status')
# def reset_payed_status():
#     print 'STARTING'
#     models.UserDebt.clear_all_payed_status()
#     print 'FINISHED'
