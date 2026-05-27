# 抖音云官方国内 Python 镜像（绝对不是 Docker Hub）
FROM public-cn-beijing.cr.volces.com/public/python:3.9.15

WORKDIR /app

# 先把依赖文件复制进来
COPY requirements.txt .

# pip 用清华源，加超时和重试
RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --default-timeout=100 \
    --retries 3 \
    -r requirements.txt

# 复制全部代码
COPY . .

EXPOSE 8000

CMD ["python", "server.py"]
