FROM python:3.13-slim
WORKDIR /app
COPY src ./src
RUN useradd --system --uid 10001 --create-home habitat && mkdir -p /app/data && chown habitat:habitat /app/data
USER 10001:10001
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/readyz', timeout=2)"]
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
CMD ["python", "-m", "cyber_habitat", "--db", "/app/data/world.sqlite3", "serve", "--host", "0.0.0.0", "--port", "8765"]
