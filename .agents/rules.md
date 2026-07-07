# Consortium Sparse Engine — Codebuff Rules

## Project Overview

Multi-component scaffold for sparse-aware deep learning with Soroban blockchain integration.

- **Language**: Python 3.11+ (core), Rust (contracts), JavaScript (frontend)
- **Package manager**: pip (Python), npm (frontend), cargo (Rust)
- **Linter/formatter**: ruff (configured in `pyproject.toml`)
- **Pre-commit**: configured via `.pre-commit-config.yaml`
- **Testing**: pytest (39 tests across `tests/`)

## Project Structure

```
consparse/         — Core ML package (PyTorch models, data, training CLI)
backend/           — FastAPI server + Soroban client helpers
  app/main.py      — API endpoints: /predict, /record_on_chain, /status, /health
  soroban_client.py — Soroban contract invocation (CLI + SDK fallback)
  scripts/         — deploy, smoke test, RPC check, record helpers
frontend/          — Vite + React demo app (App.jsx)
contracts/         — Soroban smart contract (Rust, compiles to WASM)
tests/             — pytest suite (test_consparse.py, test_backend_api.py, etc.)
configs/           — YAML training configs
scripts/           — launch_services.py (daemon launcher for backend + frontend)
```

## Key Commands

```bash
# Install & setup
pip install -r requirements.txt -r backend/requirements.txt pytest
cd frontend && npm install && cd ..
pre-commit install

# Lint & format
ruff check --fix
ruff format

# Tests
pytest -q

# Local dev (services)
python scripts/launch_services.py

# Docker
docker compose up --build -d
docker compose down

# Contract (needs Rust + stellar CLI)
cd contracts
cargo build --target wasm32v1-none --release
stellar contract deploy --wasm target/wasm32v1-none/release/consparse_contract.wasm --source-account <SECRET> --network testnet
```

## Coding Conventions

- **Python**: ruff-configured (E, W, F, I, N, UP, B, SIM), line length 120, double quotes
- **Imports**: isort-organized, `consparse` and `backend` are first-party
- **Type hints**: use modern syntax (`dict[str, int]`, `str | None`)
- **Lazy imports**: defer heavy deps (torch) inside functions when possible
- **Naming**: snake_case for functions/vars, PascalCase for classes
- **File ignores**: `backend/soroban_client_sdk.py` allows N806 (SDK class-name lookups)
- **Testing**: use pytest fixtures, 7 test classes in `tests/test_consparse.py`

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CONS_CONTRACT_ID` | — | Deployed Soroban contract ID |
| `CONS_SOROBAN_RPC` | `https://soroban-testnet.stellar.org` | Soroban RPC endpoint |
| `CONS_SIGNER_SECRET` | — | Secret key for signing txs |
| `INPUT_DIM` | `100000` | Model input dimension |
| `SKIP_MODEL_LOAD` | `0` | Skip torch model loading for smoke tests |
| `ADMIN_TOKEN` | — | Protects `/admin/set_contract` |

## CI/CD

- **CI** (`.github/workflows/ci.yml`): lint (ruff) + test (pytest) on every push/PR
- **Fullstack CI** (`.github/workflows/fullstack-ci.yml`): contract build + backend tests + frontend build
- **Docker Publish** (`.github/workflows/docker-publish.yml`): builds and pushes to `ghcr.io` on release
- **Soroban Deploy** (`.github/workflows/deploy-soroban.yml`): manual contract deployment to testnet

## Architecture Notes

- The backend's `/predict` endpoint uses lazy torch imports — works in lightweight mode with `SKIP_MODEL_LOAD=1`
- `record_on_chain` tries SDK first, falls back to CLI (stellar/soroban v27 format)
- Frontend reads `VITE_API_URL` env var at build time, falls back to `http://localhost:8000`
- The Soroban contract uses `#[contract]` + `#[contractimpl]` pattern (SDK v27)
- Contract stores `BytesN<32>` → `i128` key-value pairs
- Docker builds from repo root to include the `consparse` package in backend images
