FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY server.py .
COPY http_server.py .

RUN pip install --no-cache-dir "mcp[cli]>=1.6.0" "httpx>=0.27.0" "pydantic>=2.0.0" "fastapi>=0.104.0" "uvicorn>=0.24.0"

EXPOSE 3000

CMD ["python", "http_server.py"]
