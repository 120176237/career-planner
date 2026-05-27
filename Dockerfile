FROM public-cn-beijing.cr.volces.com/public/python:3.9.15

WORKDIR /app

COPY . .

# 直接在这里安装，不依赖 requirements.txt
RUN pip install --no-cache-dir \
    fastapi uvicorn python-multipart \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

EXPOSE 8000

CMD ["python", "server.py"]
