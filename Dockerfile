FROM public-cn-beijing.cr.volces.com/public/python:3.9.15

# 抖音云要求的工作目录
WORKDIR /opt/application

# 复制你的代码
COPY . .

# 安装依赖（使用抖音云官方源）
RUN pip install --no-cache-dir fastapi uvicorn \
    -i https://mirrors.volces.com/pypi/simple/

# 创建抖音云需要的启动脚本
RUN echo '#!/bin/bash\nuvicorn server:app --host 0.0.0.0 --port 8000' > /opt/application/run.sh \
    && chmod +x /opt/application/run.sh

# 暴露端口
EXPOSE 8000
