import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))

from flask import Flask
from settings.default import DefaultConfig

# 导入定时任务模块
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

def create_flask_app(config, enable_config_file=False):
    """
    创建Flask应用
    :param config: 配置信息对象
    :param enable_config_file: 是否允许运行环境中的配置文件覆盖已加载的配置信息
    :return: Flask应用
    """
    app = Flask(__name__)
    app.config.from_object(config)
    if enable_config_file:
        from utils import constants
        app.config.from_envvar(constants.GLOBAL_SETTING_ENV_NAME, silent=True)

    return app


def create_app(config, enable_config_file=False):
    """
    创建应用
    :param config: 配置信息对象
    :param enable_config_file: 是否允许运行环境中的配置文件覆盖已加载的配置信息
    :return: 应用
    """
    app = create_flask_app(config, enable_config_file)

    # 配置日志
    #from utils.logging import create_logger
    #create_logger(app)

    # 实现定时任务
    exec = {
        'default': ThreadPoolExecutor(max_workers=1)
    }

    app.scheduler = BackgroundScheduler(executor=exec)
    # 每分钟执行一次
    from task.aps_gradio import fix_audio
    app.scheduler.add_job(fix_audio, 'interval', minutes=1, args=[app])
    # 启动定时任务
    app.scheduler.start()

    return app


# 启动 Flask 服务器
if __name__ == "__main__":
    app = create_app(DefaultConfig, enable_config_file=True)
    app.run(debug=False)
