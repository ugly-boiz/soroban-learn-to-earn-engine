#![no_std]

use soroban_sdk::{contractimpl, Env, BytesN};

pub struct ConsparseContract;

#[contractimpl]
impl ConsparseContract {
    pub fn store_result(env: Env, key: BytesN<32>, value: i128) {
        env.storage().set(&key, &value);
    }

    pub fn get_result(env: Env, key: BytesN<32>) -> i128 {
        env.storage().get(&key).unwrap_or(0_i128)
    }
}

mod test {
    // Unit tests for Soroban contracts run with `cargo test` using soroban-sdk test helpers.
}


#[cfg(test)]
mod tests {
    use super::*;
    use soroban_sdk::{Env, BytesN};

    #[test]
    fn test_store_get() {
        let env = Env::default();
        let key = BytesN::from_array(&env, &[0u8; 32]);
        ConsparseContract::store_result(env.clone(), key.clone(), 42_i128);
        let r = ConsparseContract::get_result(env.clone(), key);
        assert_eq!(r, 42_i128);
    }
}
