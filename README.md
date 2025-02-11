## Prerequisites

- Python 3.12
- PostgreSQL.
- redis (optional).
---

## Installation

### Step 1: Setup uv
```bash
$  curl -LsSf https://astral.sh/uv/install.sh | sh
$  uv venv
$  source .venv/bin/activate
```


### Step 2: Install Dependencies

```bash
$  uv pip install --requirements pyproject.toml
```
Note: uv will install requirements on app startup so this step is optional



### Step 2: Set Up Environment Variables
```bash
$  cp .env.sample .env
```


### Step 3: Initialize the Database
Run the database migrations:
```bash
$ alembic revision --autogenerate -m "some comment"
$ alembic upgrade head
```

---

## Running the Application

```bash
$ uv run main.py
```

### Access the API
```
host:port/docs
```



