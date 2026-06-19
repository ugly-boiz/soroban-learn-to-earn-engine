Soroban Testnet setup and env vars

Required environment variables

- CONS_SOROBAN_RPC: Soroban RPC URL (default: https://soroban-testnet.stellar.org)
- CONS_CONTRACT_ID: Deployed contract ID to call (no default; set after deploying your contract)
- CONS_SIGNER_SECRET: Secret key used to sign transactions (keep this private; use a secrets manager in production)
- INPUT_DIM: Optional, model input dim (default: 100000)

Docker / docker-compose

The repository's `docker-compose.yml` exposes placeholders. Set `CONS_CONTRACT_ID` and `CONS_SIGNER_SECRET` before launching, for example by editing the file or injecting env vars at deploy time.

Deploy contract (example using `soroban` CLI)

```bash
cd contracts
# build wasm
soroban contract build
# deploy to testnet; the CLI prints a contract id
soroban contract deploy --wasm target/wasm32-unknown-unknown/release/consparse_contract.wasm --network https://soroban-testnet.stellar.org
# copy the returned CONTRACT_ID and set as CONS_CONTRACT_ID for the backend
```

CI deploy option

You can also deploy via the included GitHub Actions workflow: `.github/workflows/deploy-soroban.yml`.
Run the workflow manually from the Actions tab and provide the `CONS_SOROBAN_SECRET` repository secret. The workflow captures the deploy stdout and exposes it as a workflow output (`contract_deploy_output`) — inspect the workflow run logs/outputs to retrieve the deployed contract id.


Run backend locally (skip model load for quick smoke checks)

Linux / macOS:

```bash
export CONS_SOROBAN_RPC=https://soroban-testnet.stellar.org
export CONS_CONTRACT_ID=YOUR_CONTRACT_ID_HERE
export CONS_SIGNER_SECRET="<secret>"
export SKIP_MODEL_LOAD=1
python -m pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Windows (PowerShell):

```powershell
$env:CONS_SOROBAN_RPC = 'https://soroban-testnet.stellar.org'
$env:CONS_CONTRACT_ID = 'YOUR_CONTRACT_ID_HERE'
$env:CONS_SIGNER_SECRET = '<secret>'
$env:SKIP_MODEL_LOAD = '1'
python -m pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Frontend dev

```bash
cd frontend
npm install
npm run dev
# open the Vite dev server (default http://localhost:5173)
```

Smoke test (backend RPC reachability)

Once the backend is running, call the status endpoint:

```bash
curl http://localhost:8000/status
```

If you obtain a deployed `CONTRACT_ID` (from the CLI or GitHub Actions), you can set it at runtime using the admin endpoint (development only):

```bash
# replace <ADMIN_TOKEN> with your value if you set one in the backend environment
curl -X POST -H "Content-Type: application/json" -d '{"contract_id":"<CONTRACT_ID>", "admin_token":"<ADMIN_TOKEN>"}' http://localhost:8000/admin/set_contract
```

This returns JSON including the RPC URL and a `reachable` flag indicating whether the backend could reach the configured Soroban RPC.

Security notes

- Do not commit `CONS_SIGNER_SECRET` to source control. Use environment variables, secrets managers, or runtime injection.
- The current backend implementation uses the `soroban` CLI by default; for production replace this with a secure SDK-based signer.
