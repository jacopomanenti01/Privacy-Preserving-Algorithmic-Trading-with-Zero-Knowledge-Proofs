# Alpaca api for stocks
from alpaca.data import StockHistoricalDataClient, StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Alpaca api for crypto

from alpaca.data.live.crypto import CryptoDataStream
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest

import datetime
import pandas as pd



class GetHistoricalBars():

    def __init__(self, ticker, api_key,api_secret ):
        self.ticker = ticker
        self.params = None
        self.stock_data_client = StockHistoricalDataClient(api_key, api_secret)


    def build_params(self, delta):
        end = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=20)
        # Get current time
        now = datetime.datetime.now(datetime.timezone.utc)
        # Start from the previous trading day to ensure we have data
        #end = now - datetime.timedelta(days=1)
        start = end - datetime.timedelta(minutes=delta)

        print(f"Requesting data from {start} to {end}")

        request_params = StockBarsRequest(
            symbol_or_symbols=self.ticker,
            timeframe = TimeFrame.Minute,
            start = start,
            end = end
            )
        self.params=request_params
        
        '''
        
        request_params = CryptoBarsRequest(
            symbol_or_symbols=ticker,
            timeframe = TimeFrame.Minute,
            start = end - datetime.timedelta(minutes=100),
            end = end
            )
        
        bars = cryto_data_client.get_crypto_bars(request_params=request_params)

        '''  
    def retreive_historical_bars(self, delta):  
        self.build_params(delta)
        bars = self.stock_data_client.get_stock_bars(self.params)
        bars_pd = pd.DataFrame(dict(bar) for bar in bars[self.ticker])

        print(f"historical dataframe: \n{bars_pd}")
        return bars_pd
