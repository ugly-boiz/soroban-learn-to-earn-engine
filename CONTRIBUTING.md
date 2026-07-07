# Contributing to Consortium Sparse Engine

Thanks for contributing! This guide covers everything you need to set up a development
environment and submit changes.

## Quickstart

```bash
# 1. Clone and set up Python
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt -r backend/requirements.txt

# 2. Set up the frontend
cd frontend && npm install && cd ..

# 3. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 4. Run tests to verify
pytest -q
```

## Development Environment

### Python (Backend + ML)

- **Python 3.11+** required
- Use a virtual environment (`.venv/` is gitignored)
- Core deps in `requirements.txt` (torch, numpy, pyyaml) and `backend/requirements.txt` (fastapi, uvicorn, pydantic, stellar-sdk)
- The `consparse/` package contains the ML models and is importable from the project root

### Frontend

- **Node 18+** required
- Vite + React 18 (`frontend/`)
- `npm install` from the `frontend/` directory
- Dev server runs on port 5173, connects to backend on port 8000

### Rust / Soroban (Contracts)

- **Rust 1.84+** with `wasm32v1-none` target: `rustup target add wasm32v1-none`
- **Stellar CLI v27+**: download from [GitHub releases](https://github.com/stellar/stellar-cli/releases)
- Build: `cd contracts && cargo build --target wasm32v1-none --release`
- `soroban.toml` is pre-configured for testnet

## Running Locally

### Option 1: Shell scripts

```bash
python scripts/launch_services.py
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

With the model loaded (slower startup):
```bash
SKIP_MODEL_LOAD=0 python scripts/launch_services.py
```

### Option 2: Docker Compose

```bash
docker compose up --build -d
docker compose down          # tear down
```

Docker Compose builds both services from the project root context and starts
them with health checks. Environment variables are read from `.env` (optional).

## Code Quality

### Linting & Formatting

We use **ruff** with rules configured in `pyproject.toml`:

```bash
ruff check --fix   # auto-fix lint issues
ruff format        # format code
ruff check         # check only (CI mode)
ruff format --check
```

Ruff rules: pycodestyle (E, W), Pyflakes (F), isort (I), pep8-naming (N),
pyupgrade (UP), flake8-bugbear (B), flake8-simplify (SIM).
Line length: 120. Quote style: double.

### Pre-commit Hooks

After running `pre-commit install`, the following run automatically on `git commit`:

- `ruff` (lint + auto-fix)
- `ruff-format`
- `trailing-whitespace`, `end-of-file-fixer`
- `check-yaml`, `check-toml`, `check-json`
- `check-added-large-files`, `detect-private-key`
- `mixed-line-ending` (LF)

Run manually against all files: `pre-commit run --all-files`

### Pre-push Checklist

Before pushing, run:

```bash
ruff check              # must pass (0 errors)
ruff format --check     # must pass (all files formatted)
pytest -q               # must pass
```

These same checks run in CI (`.github/workflows/ci.yml`) on every push and PR.

## Testing

- 39 tests across `tests/`: models, data, training loop, backend API, Soroban client
- Run all: `pytest -q`
- Run a subset: `pytest tests/test_consparse.py -v`
- Backend tests use `SKIP_MODEL_LOAD=1` in CI for speed

Write tests for new features. Follow existing patterns:
- Use `pytest` fixtures and `monkeypatch` for mocking
- Keep ML tests small (small input dims, few epochs)
- Backend tests use `fastapi.testclient.TestClient`

## Project Structure

```
consparse/         — ML models (PyTorch), synthetic data, training CLI
backend/           — FastAPI server, Soroban client, scripts
  app/main.py      — API endpoints
  soroban_client.py — Contract invocation (CLI fallback)
frontend/          — Vite + React app
  App.jsx          — Demo UI (predict + record on-chain)
contracts/         — Soroban smart contract (Rust → WASM)
tests/             — pytest suite
configs/           — YAML training configs
scripts/           — Utility scripts (launch_services.py, etc.)
.agents/           — Codebuff rules for AI-assisted development
```

## Environment Variables

Copy [`.env.example`](.env.example) to `.env` and fill in:

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `CONS_CONTRACT_ID` | for on-chain | — | Deployed Soroban contract ID |
| `CONS_SOROBAN_RPC` | no | `https://soroban-testnet.stellar.org` | Soroban RPC URL |
| `CONS_SIGNER_SECRET` | for on-chain | — | Testnet secret key (keep private) |
| `SKIP_MODEL_LOAD` | no | `0` | Set to `1` to skip torch model loading |
| `INPUT_DIM` | no | `100000` | Model input dimension |
| `ADMIN_TOKEN` | no | — | Protects `/admin/set_contract` |

## CI/CD

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | push, PR | lint (ruff) + test (pytest) |
| `fullstack-ci.yml` | push, PR | contract build + backend tests + frontend build |
| `docker-publish.yml` | release published | builds & pushes images to `ghcr.io` |
| `deploy-soroban.yml` | manual (`workflow_dispatch`) | deploys contract to testnet |

## Docker Images

| Image | Dockerfile | Purpose |
|---|---|---|
| `backend` | `backend/Dockerfile` | FastAPI server (torch included) |
| `frontend` | `frontend/Dockerfile` | Vite dev server |
| `frontend-prod` | `frontend/Dockerfile.prod` | Vite build + Nginx (production) |
| `training` | `Dockerfile` (root) | ML training job |

All images build from the project root so the `consparse` package is available.

## Code of Conduct

Be respectful. Keep pull requests focused and include tests
when adding or changing functionality.

---

*For questions, open an issue or start a discussion.*
