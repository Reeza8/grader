# Dockerfile
FROM docker.arvancloud.ir/python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# کپی ساختار پروژه
COPY . .

# ایجاد پوشه media (اگر وجود ندارد)
RUN mkdir -p /app/media

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
