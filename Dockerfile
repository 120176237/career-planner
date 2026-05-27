# 换成抖音云国内镜像（避免 Docker Hub）
FROM public-cn-beijing.cr.volces.com/public/python:3.9.15

WORKDIR /app

COPY requirements.txt .

# pip 用清华源不变
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "server.py"]
