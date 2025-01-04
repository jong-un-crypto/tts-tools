import time
import json
from celery.utils.log import get_task_logger

from celery_tasks.main import app
from .dysms.sms_send import send_sms
from . import constants


logger = get_task_logger(__name__)

# 定义任务:
# bind：保证task对象会作为第一个参数自动传入
# name：异步任务别名
# retry_backoff：异常自动重试的时间间隔 第n次(retry_backoff × 2^(n-1))s
# max_retries：异常自动重试次数的上限
@app.task(bind=True, name='sms.send_verification_code', retry_backoff=3)
def send_verification_code(self, mobile, code):
    """
    发送短信验证码
    :param mobile: 手机号
    :param code: 验证码
    :return:
    """
    business_id = str(int(time.time())) + mobile
    try:
        resp = send_sms(business_id, mobile, constants.SMS_SIGN, constants.SMS_VERIFICATION_CODE_TEMPLATE_ID,
                        '{{"code":"{}"}}'.format(code))
    except Exception as e:
        logger.error('[send_verification_code] {}'.format(e))
        # 发生异常自动重试三次
        raise self.retry(exc=e, max_retries=3)
    resp_dict = json.loads(resp.decode('utf-8'))
    resp_code = resp_dict.get('Code', 'OK')
    if resp_code != 'OK':
        message = resp_dict.get('Message', '')
        logger.error('[send_verification_code] {}'.format(message))
        # 发生异常自动重试三次
        raise self.retry(exc=Exception(message), max_retries=3)
    logger.info('[send_verification_code] {} {}'.format(mobile, code))
