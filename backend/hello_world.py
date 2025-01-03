#from sqlalchemy  import create_engine

#engine = create_engine('mysql+pymysql://root:root@mysql:3307/db')
#print("connected")

from alpaca.trading.client import TradingClient
from alpaca.data import StockHistoricalDataClient, StockBarsRequest
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.timeframe import TimeFrame
import datetime
from alpaca.data.live import StockDataStream
from pandas_ta.momentum import rsi
import pandas as pd
from dotenv import load_dotenv
import talib
import os
import joblib
from collections import deque

# Internal Imports
from utils.feature import features_extraction
from utils.prediction import trend_classification

# load env variables
load_dotenv()
api_key = os.getenv("ALPACA_API_KEY")
api_secret = os.getenv("ALPACA_API_SECRET")


# Connect to alpaca trading account
trading_client = TradingClient(api_key, api_secret)
stock_data_client = StockHistoricalDataClient(api_key, api_secret)

# define trading parameters for RSI
OVERBOUGHT_THRESH = 60
OVERSOLD_THRESH = 40
CLOSE_POSITION_THRESH = 50
ticker = "AAPL"

# initialize the model
repo_root = os.path.dirname(os.path.dirname(__file__))
path = os.path.join(repo_root, "Test", "mlModel", "best_model_xboost.joblib")
print(path)



model = joblib.load(path)

# helper function for placing the market order
def place_market_order(side):
    order_data = MarketOrderRequest(
        symbol = "AAPL",
        qty = 1,
        side = side,
        time_in_force = TimeInForce.GTC # see other options
    )

    return trading_client.submit_order(order_data=order_data)

def close_position():
     return trading_client.close_all_positions(True)

def get_historical_data(ticker):
    print("Retriving data")
    end = datetime.datetime(2024,12,31,19,22)

    request_params = StockBarsRequest(
        symbol_or_symbols=ticker,
        timeframe = TimeFrame.Minute,
        start = end - datetime.timedelta(minutes=49),
        end = end
        )
    
    bars = stock_data_client.get_stock_bars(request_params=request_params)
    bars_pd = pd.DataFrame(dict(bar) for bar in bars[ticker])

    print(f"historical dataframe: {bars_pd}")
    return bars_pd



bars = get_historical_data(ticker)

has_position = False
is_long  = False
is_short = False


async def on_new_bar(bar):
   global bars
   global has_position


   #bars.append(bar)
   print("New bar!")
   bar_df = pd.DataFrame([dict(bar)])
   df = pd.concat([bars, bar_df], ignore_index=True)

   

   if len(bars)>=50: # Need at least 50 bars to calculate SMA_50 (check feature.py in utils folder)
     print(df)
     # Calculate Latest RSI
     #rsi_value = rsi(df['close'].tail(14))
     rsi_value = talib.RSI(df['close'], timeperiod=14).iloc[-1]
     print(f"RSI IS {rsi_value}")

     features = features_extraction(df)
     print(features)

     prediction = trend_classification(features, model)
     print(prediction)

     # Trading logic

     if rsi_value<=OVERSOLD_THRESH and not has_position:
            print("attempting to buy")
            place_market_order(OrderSide.BUY)
            has_position = True
            is_long = True
            print("buy completed")

     elif rsi_value<=OVERSOLD_THRESH and has_position:
            print("closing position")
            has_position = False
            is_long = False

            # close
            close_position()
            print("position close")

     elif rsi_value>=OVERBOUGHT_THRESH and has_position:
            print("closing position")

            has_position = False
            is_long = False

            # close
            close_position()
            print("position close")
    
   # drop the first row and ensures bars always maintains exactly 50 rows.
   #bars = df.iloc[1:].reset_index(drop=True)
   bars = df.tail(50).reset_index(drop=True)




# Streaming real data
stream = StockDataStream(api_key,api_secret)
stream.subscribe_bars(on_new_bar, 
                        "AAPL")
# 1 minute bars
stream.run()

'''
- RSI: 14 days back 
- Test slow
- Few trades

-  strategy 1m timeframe
-  test with data >09/2024
'''