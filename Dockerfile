FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --no-deps .
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "cyber_habitat", "--db", "/app/data/world.sqlite3", "demo"]
