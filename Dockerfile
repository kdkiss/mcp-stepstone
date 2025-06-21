FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir jsonrpcserver beautifulsoup4 requests

ENTRYPOINT ["python3", "mcp_server.py"]