Backend integration notes

Env vars (set in your environment or Docker):

- `CONS_CONTRACT_ID`: deployed Soroban contract ID
- `CONS_SOROBAN_RPC`: soroban RPC endpoint (default: https://soroban-testnet.stellar.org)
- `INPUT_DIM`: model input dimension for synthetic demo (default: 100000)

Record-on-chain endpoint (`POST /record_on_chain`) will call the helper script
`backend/scripts/record_on_chain.py`. Replace the placeholder implementation with a
secure signing flow when deploying to production.

To deploy the contract (convenience wrapper):

```bash
python backend/scripts/deploy_contract.py
```

API examples

Health check

```bash
curl http://localhost:8000/health
```

Predict (POST JSON):

```bash
curl -X POST -H "Content-Type: application/json" -d '{"batch_size":4}' http://localhost:8000/predict
```

Record a numeric result on-chain (POST raw JSON number):

```bash
curl -X POST -H "Content-Type: application/json" -d 123.4 http://localhost:8000/record_on_chain
```

Notes

- `record_on_chain` attempts to use the `soroban` CLI or a helper module.
- Do not place private keys in the repo. Use environment variables or a
	secrets manager for `CONS_SOROBAN_SECRET` and similar values.
