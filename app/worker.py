
from app.initialize import wat_worker
from app import models


@wat_worker.task(name='wat_worker.check_expiring_debt')
def check_expiring_debt():
    print 'STARTING'
    print 'FINISHED'


@wat_worker.task(name='wat_worker.reset_payed_status')
def reset_payed_status():
    print 'STARTING'
    models.UserDebt.clear_all_payed_status()
    print 'FINISHED'
