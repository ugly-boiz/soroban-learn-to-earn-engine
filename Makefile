install:
	python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt

run-backend:
	python -m uvicorn backend.app.main:app --reload --port 8000

test:
	pytest -q

deploy-contract:
	python backend/scripts/deploy_contract.py
