# 使用 Python 3.11 作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY src/ /app/src/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r src/requirements.txt

# 设置环境变量
ENV PYTHONPATH=/app/src

# 暴露端口
EXPOSE 8000

# 设置工作目录为 src
WORKDIR /app/src

# 设置启动命令
CMD ["python", "webpage/run_web.py"] 