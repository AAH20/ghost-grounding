FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir pydantic pillow pytest

COPY ghost_grounding/ ./ghost_grounding/
COPY tests/ ./tests/

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["ghost-grounding"]
CMD ["benchmark"]
