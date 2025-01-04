# Celery

一个简单、灵活且可靠、处理大量消息的分布式系统，可以在一台或者多台机器上运行。
单个 Celery 进程每分钟可处理数以百万计的任务。
通过消息进行通信，使用消息队列（broker）在客户端和消费者之间进行协调

# 安装cli

```bash
sudo apt install python-celery-common
```

# 启动Celery服务

```bash
cd tts-tools
celery -A app.celery_tasks.main worker -l info
* -A指对应的应用程序, 其参数是项目中 Celery实例的位置。
* worker指这里要启动的worker。
* -l指日志等级，比如info等级。
```

# worker 工作模式

进程池模式: 默认模式以当前cores 4X进程池, 手动指定如4个 `celery worker -A proj --concurrency=4`
协程模式: pip install eventlet && celery -A celery_tasks.main worker -l info -P eventlet -c 1000
