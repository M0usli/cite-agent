FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/models

WORKDIR /app

# CPU-only PyTorch first: the default wheel bundles CUDA and is several GB larger.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir -e ".[embeddings,dev]"

COPY . .

EXPOSE 8000
# Apply database migrations, then start the API with hot reload (development).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
