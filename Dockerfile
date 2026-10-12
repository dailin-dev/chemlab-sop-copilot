FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 最小构建工具，防止个别依赖在 slim 上需要编译
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖，利用分层缓存
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 复制代码与处理后的小数据（元数据 + chunks），不复制 PDF / 向量库
COPY src ./src
COPY data/processed ./data/processed
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]