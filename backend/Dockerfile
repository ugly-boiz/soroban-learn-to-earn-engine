# =============================================================================
# Consortium Sparse Engine — Backend Service
# =============================================================================
# Build from the project root so the consparse package is available:
#   docker build -f backend/Dockerfile -t consparse-backend .
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# Install system deps needed for torch
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install root dependencies (torch, numpy, pyyaml, etc.)
COPY requirements.txt /app/requirements-root.txt
RUN pip install --no-cache-dir -r /app/requirements-root.txt

# Install backend-specific dependencies (fastapi, uvicorn, etc.)
COPY backend/requirements.txt /app/requirements-backend.txt
RUN pip install --no-cache-dir -r /app/requirements-backend.txt

# Copy the consparse package (needed by backend model loading)
COPY consparse/ /app/consparse/

# Copy backend source
COPY backend/ /app/backend/

# Copy setup.py for package metadata
COPY setup.py /app/
COPY pyproject.toml /app/

# Set Python path so consparse is importable
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
