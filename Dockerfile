FROM public-cn-beijing.cr.volces.com/public/python:3.9.15

WORKDIR /app
COPY . .

# 不使用任何国内源！！！
RUN pip install --no-cache-dir fastapi uvicorn

EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
