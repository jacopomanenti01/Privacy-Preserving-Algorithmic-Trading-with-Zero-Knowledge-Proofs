import hashlib
from utils.get_hash import Getter
from zkproof_forge.utils.model_hash import compute_model_hash
from Proover import prove
import os
import asyncio
import talib
import pandas as pd
import sys
from dotenv import load_dotenv
import pytz
import datetime
import joblib







class ZkProof():

    def __init__(self, ticker, day):
        self.day = day
        self.delta = 49
        self.hash_from_smart = None
        self.hash_computed = compute_model_hash()
        self.prediction = self.initialize_prediction()
        self.model = self.initialize_model()
        self.features = self.initialize_features()

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
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(project_root)
        sys.path.append(project_root)  # Add project root to Python path
    
        # Now we can import the class
        from backend.utils.historical_bars import GetHistoricalBars
        return GetHistoricalBars(ticker,api_key, api_secret)

    def initialize_data(self):
        return self.broker.retreive_historical_bars(self.delta, self.day )
        
    def initialize_prediction(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(project_root)
        sys.path.append(project_root)  # Add project root to Python path
    
        # Now we can import the class
        from backend.utils.prediction import trend_classification
        return trend_classification
    
    def initialize_model(self):
        repo_root = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(repo_root, "Test", "mlModel", "best_model_xboost.joblib")
        print(f"Model in path: {path}")
        model = joblib.load(path)
        return model


    def initialize_features(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(project_root)
        sys.path.append(project_root)  # Add project root to Python path
    
        # Now we can import the class
        from backend.utils.feature import features_extraction
        return features_extraction



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



    

    


    def rsi(self):
        rsi_value = round(talib.RSI(self.data['close'], timeperiod=14).iloc[-1],2)
        return rsi_value
    
    def get_return_per_day(self,date):
        pass

  

    async def main(self):
        await self.set_hash_from_smart()
        check = self.check_hash()

        print(f"checking model hash:{check}")

        if check:

            features = self.features(self.data)
            prediction =  self.prediction(features, self.model)

            print(f"Prediction is {prediction}")
            current_path = os.getcwd()
            print(f"calling the function from {current_path}")
            oversold_threshold = os.getenv("OVERSOLD_THRESHOLD")
            overbought_threshold = os.getenv("OVERBOUGHT_THRESHOLD")
            thresh = os.getenv("THRESH")
            proof = await prove(
                rsi = int(self.rsi()),
                prediction = prediction,
                oversold_threshold = oversold_threshold,
                overbought_threshold = overbought_threshold,
                haspos = 0,
                ret = 10,
                thresh = thresh
            )
            
            print(f"Trade has been verified, resul is: {proof}")
            return proof






if __name__ == "__main__":
    et = pytz.timezone('US/Eastern')
    market_time = datetime.datetime(2024, 1, 11, 10, 0)  # Year, Month, Day, Hour, Minute
    utc_time = et.localize(market_time).astimezone(pytz.UTC)

    print(utc_time)  
    zkproof = ZkProof("AAPL", utc_time)
    asyncio.run(zkproof.main())

