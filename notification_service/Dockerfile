FROM python:3.12-slim

WORKDIR /app

RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        make curl gettext \
        # Required for python-snappy (Kafka compression)
        libsnappy-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && mv /root/.local/bin/uvx /usr/local/bin/uvx

COPY pyproject.toml uv.lock /app/

RUN uv pip install --system --no-cache .

COPY /app /app
RUN chown -R appuser:appgroup /app
USER appuser

# Expose port for AsyncAPI documentation
EXPOSE 11111

# Run FastStream ASGI app with uvicorn (includes AsyncAPI docs)
# - main:asgi_app because WORKDIR=/app and main.py is directly in /app/
# - Docs available at http://localhost:11111/
# - Health check at http://localhost:11111/health
CMD ["uvicorn", "main:asgi_app", "--host", "0.0.0.0", "--port", "11111"]
