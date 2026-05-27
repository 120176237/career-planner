FROM public-cn-beijing.cr.volces.com/public/python:3.9.15

WORKDIR /app
COPY . .

# 关键：使用抖音云官方内部 PyPI 源，不超时！
RUN pip install --no-cache-dir fastapi uvicorn \
    -i https://mirrors.volces.com/pypi/simple/

EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
