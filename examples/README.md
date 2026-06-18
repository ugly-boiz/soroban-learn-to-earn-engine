Examples for Consortium Sparse Engine

Prerequisites

- Backend running at http://localhost:8000 (see README)
- Python 3.11+ for example scripts

Call predict (Python)

```bash
python examples/call_predict.py
```

Call record on chain (Python)

```bash
python examples/call_record.py
```

cURL

Health check:

```bash
curl http://localhost:8000/health
```

Predict:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"batch_size":4}' http://localhost:8000/predict
```

Record on-chain (example, JSON float body):

```bash
curl -X POST -H "Content-Type: application/json" -d 123.4 http://localhost:8000/record_on_chain
```
