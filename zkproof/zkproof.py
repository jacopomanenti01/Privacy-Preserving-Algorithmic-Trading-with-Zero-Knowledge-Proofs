import hashlib
from utils.get_hash import Getter
from zkproof_forge.utils.model_hash import compute_model_hash
import os
import asyncio
import talib
import pandas as pd
import sys
from dotenv import load_dotenv
import pytz
import datetime





class ZkProof():

    def __init__(self, ticker, day):
        self.day = day
        self.delta = 15
        self.hash_from_smart = None
        self.hash_computed = compute_model_hash()

        # Load environment variables
        dir_path = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(dir_path, "zkproof_forge", ".env")
        load_dotenv(env_path)

        # mmmm
        api_key = os.getenv("ALPACA_API_KEY")
        api_secret = os.getenv("ALPACA_API_SECRET")
        print(api_key)
        print(api_secret)

        self.broker = self.initialize_broker(ticker,api_key, api_secret)
        self.data =  self.initialize_data()

    def initialize_broker(self, ticker, api_key, api_secret):
        pass
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(project_root)
        sys.path.append(project_root)  # Add project root to Python path
    
        # Now we can import the class
        from backend.utils.historical_bars import GetHistoricalBars
        return GetHistoricalBars(ticker,api_key, api_secret)

    def initialize_data(self):
        return self.broker.retreive_historical_bars(self.delta, self.day )
        

    async def set_hash_from_smart(self):
        getter = Getter()
        hash = await getter.get_hash()

        self.hash_from_smart = hash
    


    def check_hash(self):
        address = os.getenv("CONTRACT_ADDRES")
        print(f"Checking Model Hashed with Hash stored in smart contract {address}")
        check = self.hash_from_smart == self.hash_computed
        print(f"Check result {check}")

        return check

    async def main(self):
        await self.set_hash_from_smart()
        check = self.check_hash()

        print(self.rsi())

    

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


    def rsi(self):
        rsi_value = round(talib.RSI(self.data['close'], timeperiod=14).iloc[-1],2)
        return rsi_value

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
    et = pytz.timezone('US/Eastern')
    market_time = datetime.datetime(2024, 1, 11, 10, 0)  # Year, Month, Day, Hour, Minute
    utc_time = et.localize(market_time).astimezone(pytz.UTC)

    print(utc_time)  
    zkproof = ZkProof("AAPL", utc_time)
    asyncio.run(zkproof.main())

