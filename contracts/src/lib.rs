#![no_std]

use soroban_sdk::{contract, contractimpl, Env, BytesN};

#[contract]
pub struct ConsparseContract;

#[contractimpl]
impl ConsparseContract {
    pub fn store_result(env: Env, key: BytesN<32>, value: i128) {
        env.storage().instance().set(&key, &value);
    }

    pub fn get_result(env: Env, key: BytesN<32>) -> i128 {
        env.storage().instance().get(&key).unwrap_or(0_i128)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use soroban_sdk::{Env, BytesN};

    #[test]
    fn test_store_get() {
        let env = Env::default();
        let contract_id = env.register(ConsparseContract, ());
        let client = ConsparseContractClient::new(&env, &contract_id);

        let key = BytesN::from_array(&env, &[0u8; 32]);
        client.store_result(&key, &42_i128);
        let r = client.get_result(&key);
        assert_eq!(r, 42_i128);
    }
}
