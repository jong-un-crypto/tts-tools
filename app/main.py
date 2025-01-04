import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))

from flask import Flask, jsonify
from settings.default import DefaultConfig

from redis.exceptions import RedisError

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

    # 限流器
    from utils.limiter import limiter as lmt
    lmt.init_app(app)

    # 注册url转换器
    from utils.converters import register_converters
    register_converters(app)

    from redis.sentinel import Sentinel
    _sentinel = Sentinel(app.config['REDIS_SENTINELS'])
    app.redis_master = _sentinel.master_for(
        app.config['REDIS_SENTINEL_SERVICE_NAME'])
    app.redis_slave = _sentinel.slave_for(
        app.config['REDIS_SENTINEL_SERVICE_NAME'])

    # """
    # https://redis.io/docs/clients/python/
    # https://redis-py.readthedocs.io/en/stable/clustering.html
    # """
    # from redis.cluster import RedisCluster
    # from redis.cluster import ClusterNode
    # nodes = []
    # for node in app.config['REDIS_CLUSTER']:
    #     nodes.append(ClusterNode(node['host'], node['port']))
    # app.redis_cluster = RedisCluster(
    #     startup_nodes=nodes, password='1234')

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

    # # 添加请求钩子
    from utils.middlewares import jwt_authentication
    app.before_request(jwt_authentication)

    # 注册用户模块
    from .resources.user import user_bp
    app.register_blueprint(user_bp)

    return app


@app.route('/')
def route_map():
    """
    main view, 返回所有视图url
    """
    rules_iterator = app.url_map.iter_rules()
    return jsonify({rule.endpoint: rule.rule for rule in rules_iterator if rule.endpoint not in ('route_map', 'static')})

# 启动 Flask 服务器
if __name__ == "__main__":
    app = create_app(DefaultConfig, enable_config_file=True)
    app.run(debug=False)
