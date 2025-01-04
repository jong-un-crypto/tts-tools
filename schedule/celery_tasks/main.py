# celery启动文件
from celery import Celery
from settings.default import CeleryConfig

# 创建celery实例
app = Celery('toutiao')
# 加载celery配置
app.config_from_object(CeleryConfig)
app.config_from_envvar('TOUTIAO_CELERY_SETTINGS', silent=True)
# 自动注册celery任务
app.autodiscover_tasks(['celery_tasks.sms'])
