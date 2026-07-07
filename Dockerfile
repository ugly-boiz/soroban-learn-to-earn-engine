# =============================================================================
# Consortium Sparse Engine — Training Container
# =============================================================================
# Standalone training job:
#   docker build -t consparse-train .
#   docker run consparse-train
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY consparse/ ./consparse/
COPY configs/ ./configs/
COPY setup.py pyproject.toml ./

ENV PYTHONPATH=/app

CMD ["python", "-m", "consparse.train", "--config", "configs/dev.yaml"]
