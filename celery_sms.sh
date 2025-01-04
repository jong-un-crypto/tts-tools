# 设置 Python 路径
export PYTHONPATH=/root/config:$PYTHONPATH

# 设置 Flask 环境为生产
export FLASK_ENV=production

# 进入 tts-tools 目录
cd /root/tts-tools

# 激活 Conda 环境 uvr5
source /root/miniconda3/etc/profile.d/conda.sh
conda activate uvr5

# 执行 Python 程序
exec celery -A app.celery_tasks.main worker -l info -Q sms
