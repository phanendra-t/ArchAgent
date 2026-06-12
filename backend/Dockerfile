FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gcc \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /build

COPY pyproject.toml ./
COPY app/ ./app/

RUN uv venv /app/.venv && \
    uv pip install --python /app/.venv/bin/python torch --index-url https://download.pytorch.org/whl/cpu && \
    uv pip install --python /app/.venv/bin/python -e .

RUN /app/.venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"


FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /root/.cache /root/.cache

COPY app/ ./app/

COPY tests/corpus/ ./tests/corpus/

ENV ARCHAGENT_DATA_DIR=/app/data
RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]