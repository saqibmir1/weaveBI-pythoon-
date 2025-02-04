FROM python:3.12-slim-bookworm

# Install UV and build dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (without project installation)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy project files
COPY . .

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Database migrations (running these manually inside the container for now)
# RUN alembic revision --autogenerate -m "init" || echo "not needed" && \
#     alembic upgrade head || echo "not needed"

EXPOSE 8000

CMD ["uv", "run", "main.py"]