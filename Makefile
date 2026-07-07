install:
	python -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install -r backend/requirements.txt

install-dev:
	python -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pip install -r backend/requirements.txt && .venv/bin/pip install pytest requests

run-backend:
	.venv/bin/python -m uvicorn backend.app.main:app --reload --port 8000

run-frontend:
	cd frontend && npm install && npm run dev

test:
	.venv/bin/pytest -q

deploy-contract:
	.venv/bin/python backend/scripts/deploy_contract.py

build-contract:
	cd contracts && cargo build --target wasm32-unknown-unknown --release
