FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ADD . /app/

RUN uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

RUN alembic revision --autogenerate -m "init" || echo "Alembic revision already exists"
RUN alembic upgrade head || echo "Alembic upgrade failed"

CMD ["uv", "run", "main.py"]