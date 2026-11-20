FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv \
    && pip uninstall -y pip setuptools

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

COPY . .

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 3000

CMD [".venv/bin/gunicorn", "--bind", "0.0.0.0:3000", "wsgi:app"]
