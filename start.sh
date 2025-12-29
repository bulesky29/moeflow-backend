#!/bin/bash

export CONFIG_PATH=./configs/dev.py
export FLASK_APP=manage.py
export FLASK_ENV=development

# 激活环境 (根据实际情况选择其一，此处以 conda 为例)
# 如果是 WSL 虚拟环境，请取消下面 wslvenv 的注释
conda activate moeflow
source wslvenv/bin/activate
eval "$(conda shell.bash hook)"


# 定义清理函数：按下 Ctrl+C 时停止所有后台进程
cleanup() {
    echo "Stopping all services..."
    kill $(jobs -p)
    exit
}
trap cleanup SIGINT SIGTERM

# 2. 启动 Flask 后端
echo "Starting Flask server on port 5000..."
flask run --host=0.0.0.0 --port=5000 &

# 3. 启动 Celery Default Worker
echo "Starting Celery default worker..."
celery -A app.celery worker -n default --loglevel=info &

# 4. 启动 Celery Output Worker
echo "Starting Celery output worker..."
celery -A app.celery worker -Q output -n output --loglevel=info &

# 等待所有后台进程
echo "All services are running. Press Ctrl+C to stop all."
wait