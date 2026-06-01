FROM python:3.14-rc-slim

WORKDIR /app

RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

RUN apt-get update \
    && apt-get install -y --no-install-recommends make curl gettext \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && mv /root/.local/bin/uvx /usr/local/bin/uvx

COPY pyproject.toml uv.lock /app/

RUN uv pip install --system --no-cache .

COPY /app /app
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8001

CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
