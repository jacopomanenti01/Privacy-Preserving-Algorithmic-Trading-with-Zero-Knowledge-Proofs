import hashlib
from utils.get_hash import Getter
from zkproof_forge.utils.model_hash import compute_model_hash
import os
import asyncio



class ZkProof():

    def __init__(self):
        self.hash_from_smart = None
        self.hash_computed = compute_model_hash()

    async def set_hash_from_smart(self):
        getter = Getter()
        hash = await getter.get_hash()

        self.hash_from_smart = hash

    def check_hash(self):
        address = os.getenv("CONTRACT_ADDRES")
        print(f"Checking Model Hashed with Hash stored in smart contract {address}")
        check = self.hash_from_smart == self.hash_computed
        return check

    async def main(self):
        await self.set_hash_from_smart()
        check = self.check_hash()
        print(f"Check result {check}")
    

    def generate_order_proof(self):
    # Prove:
    # 1. RSI value is correctly calculated
    # 2. Price thresholds are met
    # 3. Position size is within limits
    # 4. Stop loss/take profit are correctly set
    #rsi_proof = prove_rsi_threshold()
        
    # Strategy logic
    #prediction_proof = verify_model_output()
    #entry_conditions = verify_entry_rules()
        pass

    def verify_trading_decision(self):
    # Create circuit for:
    # 1. RSI conditions (< 40 or > 60)
    # 2. Model prediction (1 or 2)
    # 3. Position existence check
        pass


# Input: Private data (e.g., df['close'] for RSI calculation or features for prediction).
# Computation: Perform the calculations (e.g., RSI or prediction logic).
# Output: A proof that the computation is correct without revealing the input data.

# 1. Store the Model Hash on the Blockchain
# Instead of storing the full model, store a cryptographic hash of the model on the blockchain.
# When loading the model, recompute its hash and compare it to the stored hash to verify integrity.

if __name__ == "__main__":
    zkproof = ZkProof()
    asyncio.run(zkproof.main())

