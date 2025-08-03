# ---- Builder Stage ----
FROM python:3.11-slim as builder
WORKDIR /app
RUN pip install poetry
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-dev --no-root

# ---- Final Stage ----
FROM python:3.11-slim
RUN apt-get update && apt-get install -y cron supervisor
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY waste_sync.py .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
