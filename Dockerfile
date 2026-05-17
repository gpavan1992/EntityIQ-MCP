FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY server.py .
RUN pip install --no-cache-dir "mcp[cli]>=1.6.0" "httpx>=0.27.0" "pydantic>=2.0.0"
EXPOSE 8000
CMD ["python", "server.py"]
