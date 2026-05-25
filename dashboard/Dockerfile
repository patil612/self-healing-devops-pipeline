FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir psycopg2-binary 2>/dev/null || true

# Copy dashboard files
COPY dashboard_server.py .
COPY index.html .

# Copy scripts and .env from project root (mounted as volume or copied at build)
# The server needs access to scripts/ for notifier, and docker socket for jenkins config
ENV PYTHONUNBUFFERED=1

EXPOSE 3000

CMD ["python", "dashboard_server.py"]
