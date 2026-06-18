Soroban (Stellar) contract scaffold

Build and deploy (requires `soroban` CLI and Rust toolchain):

```bash
# from contracts/
cargo build --target wasm32-unknown-unknown --release
# or use soroban CLI to build and deploy to testnet
soroban contract build
soroban contract deploy --wasm target/wasm32-unknown-unknown/release/consparse_contract.wasm --network https://soroban-testnet.stellar.org
```

The contract exposes `store_result(key: BytesN<32>, value: i128)` and `get_result(key)`.
Use the `soroban` CLI or SDK to invoke these methods after deployment.

Stellar / Soroban notes

- This contract targets Stellar's Soroban smart contract platform. Use the
	`soroban` CLI to build, deploy, and invoke the contract against the
	Soroban RPC (e.g. the public testnet at `https://soroban-testnet.stellar.org`).
- The repository includes a `soroban.toml` with a `testnet` entry pointing at
	the Soroban testnet RPC. You can override the RPC URL with the
	`CONS_SOROBAN_RPC` environment variable used by the backend helpers.

Example commands (adjust `CONTRACT_ID` / secrets as needed):

```bash
cd contracts
# build wasm
cargo build --target wasm32-unknown-unknown --release

# or using soroban CLI
soroban contract build

# deploy to testnet (requires soroban CLI and a funded account / key)
# the CLI will return a contract id, set as CONS_CONTRACT_ID for the backend
soroban contract deploy --wasm target/wasm32-unknown-unknown/release/consparse_contract.wasm --network https://soroban-testnet.stellar.org

# invoke store_result
soroban contract invoke --network https://soroban-testnet.stellar.org <CONTRACT_ID> store_result 123
```

Security note: do not store secret keys in plaintext. Use GitHub Secrets, environment
variables injected at runtime, or a secure signing service when deploying from CI.
