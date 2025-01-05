#from sqlalchemy  import create_engine

#engine = create_engine('mysql+pymysql://root:root@mysql:3307/db')
#print("connected")

from alpaca.trading.client import TradingClient
from alpaca.data import StockHistoricalDataClient, StockBarsRequest
from alpaca.trading.requests import MarketOrderRequest, StopLossRequest, TakeProfitRequest, ReplaceOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus, OrderClass
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

# For crypto

from alpaca.data.live.crypto import CryptoDataStream
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest

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
cryto_data_client = CryptoHistoricalDataClient(api_key, api_secret)

# define trading parameters for RSI
OVERBOUGHT_THRESH = 60
OVERSOLD_THRESH = 40
PERC_THRESH = 3
CLOSE_POSITION_THRESH = 50
ticker = "ETH/USD"

# initialize the model
repo_root = os.path.dirname(os.path.dirname(__file__))
path = os.path.join(repo_root, "Test", "mlModel", "best_model_xboost.joblib")
print(path)



model = joblib.load(path)

# helper function for placing the market order
def place_market_order(side, take_profit, stop_loss):
    order_data = MarketOrderRequest(
        symbol = ticker,
        qty = 1,
        side = side,
        order_class = OrderClass.BRACKET, 
        time_in_force = TimeInForce.GTC,
        take_profit = take_profit,
        stop_loss = stop_loss
    )

    return trading_client.submit_order(order_data)

def close_position():
     return trading_client.close_all_positions(True)

def get_historical_data(ticker):
    print("Retriving data")
    end = datetime.datetime.utcnow()
    #datetime.datetime(2024,12,31,19,22)

    '''
    request_params = StockBarsRequest(
        symbol_or_symbols=ticker,
        timeframe = TimeFrame.Minute,
        start = end - datetime.timedelta(minutes=49),
        end = end
        )
    '''
    
    request_params = CryptoBarsRequest(
        symbol_or_symbols=ticker,
        timeframe = TimeFrame.Minute,
        start = end - datetime.timedelta(minutes=100),
        end = end
        )
    
    bars = cryto_data_client.get_crypto_bars(request_params=request_params)

    '''    
    bars = stock_data_client.get_stock_bars(request_params=request_params)
    '''
    bars_pd = pd.DataFrame(dict(bar) for bar in bars[ticker])

    print(f"historical dataframe: {bars_pd}")
    return bars_pd

def get_pl_client():
    pos_info = trading_client.get_all_positions()[0]
    plpc = float(pos_info.unrealized_plpc)*100
    return plpc

def update_position(old_take, new_take, old_stop, new_stop):
    trading_client.replace_order_by_id(old_take.id, new_take)
    trading_client.replace_order_by_id(old_stop.id, new_stop)





bars = get_historical_data(ticker)

has_position = True
is_long  = False
is_short = False
current_stop_loss= None
current_take_profit = None
tp_perc = .10
sl_perc = .04

def test_buy(price): 
    print("testing buy function")
    stop_loss = price*(1 - sl_perc)
    take_profit = price*(1 + tp_perc)
    stop_loss = StopLossRequest(stop_price = stop_loss, limit_price = stop_loss)
    take_profit = TakeProfitRequest(limit_price=take_profit)
    print(f"\nAttempting to buy at price: {price}, stop loss: {stop_loss}, take profit: {take_profit} ")

    parent_order = place_market_order(OrderSide.BUY, take_profit, stop_loss)
    print(f"Parent order:{parent_order}")
    current_take_profit = parent_order.legs[0]
    current_stop_loss = parent_order.legs[1]
    has_position = True
    is_long = True
    print(f"\nOrder placed succesfully: {parent_order}.")

    return current_take_profit, current_stop_loss, has_position

def test_update(price):
    print("Testing update function")
    plpc = get_pl_client()
    print(f"\nCurrent position plpc: {plpc}")
    if plpc >= -0.00001:
                    new_stop_loss =  price*(1 - sl_perc)
                    new_take_profit = price*(1 + tp_perc)
                    take_profit_update = ReplaceOrderRequest(limit_price=new_take_profit)
                    stop_loss_update = ReplaceOrderRequest(stop_price=new_stop_loss)
                    print(f"\nRe-entering with Take profift at:{new_take_profit} and Stop loss at: {new_stop_loss}")
                    update_position(old_take=current_take_profit, 
                                    new_take=take_profit_update,
                                    old_stop=current_stop_loss, 
                                    new_stop =stop_loss_update)
                    print("Position updated correclty")
                    return new_stop_loss, new_take_profit


async def on_new_bar(bar):
   global bars
   global has_position
   global current_stop_loss
   global current_take_profit


   #bars.append(bar)
   print("New bar!")
   bar_df = pd.DataFrame([dict(bar)])
   df = pd.concat([bars, bar_df], ignore_index=True)

   

   if len(bars)>=50: # Need at least 50 bars to calculate SMA_50 (check feature.py in utils folder)
     print(df)
     # Calculate Latest RSI

     rsi_value = talib.RSI(df['close'], timeperiod=14).iloc[-1]
     print(f"RSI IS {rsi_value}")
     price = df['close'].iloc[-1]
     print(f"Price is {price}")
     features = features_extraction(df)
     prediction = trend_classification(features, model)

     if not has_position:
        current_take_profit, current_stop_loss, has_position = test_buy(price)
     elif has_position:
        current_stop_loss, current_take_profit = test_update(price)

     # Trading logic

     if rsi_value<=OVERSOLD_THRESH:
        print(f"\nOversold condition met: current RSI is {rsi_value}<{OVERSOLD_THRESH}")
        print(f"\nCurrent trend predictin is: {prediction}")

        if prediction ==1: 
            if not has_position:
                print("\nBuy signal, as we did not have a position.")

                stop_loss = price*(1 - sl_perc)
                take_profit = price*(1 + tp_perc)
                stop_loss = StopLossRequest(stop_price = stop_loss, limit_price = stop_loss)
                take_profit = TakeProfitRequest(limit_price=take_profit)
                print(f"\nAttempting to buy at price: {price}, stop loss: {stop_loss}, take profit: {take_profit} ")

                parent_order = place_market_order(OrderSide.BUY, take_profit, stop_loss)
                current_take_profit = parent_order.legs[0]
                current_stop_loss = parent_order.legs[1]
                has_position = True
                is_long = True
                print(f"\nOrder placed succesfully: {parent_order}.")
                 

            elif has_position:
                
                plpc = get_pl_client()
                print(f"\nCurrent position plpc: {plpc}")
                if plpc >= PERC_THRESH:
                    new_stop_loss =  price*(1 - sl_perc)
                    new_take_profit = price*(1 + tp_perc)
                    take_profit_update = ReplaceOrderRequest(limit_price=new_take_profit)
                    stop_loss_update = ReplaceOrderRequest(stop_price=new_stop_loss)
                    print(f"\nRe-entering with Take profift at:{new_take_profit} and Stop loss at: {new_stop_loss}")
                    update_position(old_take=current_take_profit, 
                                    new_take=take_profit_update,
                                    old_stop=current_stop_loss, 
                                    new_stop_loss =stop_loss_update)
                    print("Position updated correclty")
                    current_stop_loss = new_stop_loss
                    current_take_profit = new_take_profit


        elif prediction == 2 and has_position == True:
            
            print("\n Sell signal, as we do have a position.")
            print(f"\nAttempting to close at price:")
            close_position()
            has_position = False
            is_long = False
            print("\nPosition closed succesfully")





     elif rsi_value>=OVERBOUGHT_THRESH:
        print(f"\nOverbought condition met: current RSI is {rsi_value}>={OVERBOUGHT_THRESH}")
        print(f"\nCurrent trend predictin is: {prediction}")

        if prediction == 1:
            if has_position:
                plpc = get_pl_client()
                print(f"\nCurrent position plpc: {plpc}")
                if plpc >= PERC_THRESH:
                    new_stop_loss =  price*(1 - sl_perc)
                    new_take_profit = price*(1 + tp_perc)
                    take_profit_update = ReplaceOrderRequest(limit_price=new_take_profit)
                    stop_loss_update = ReplaceOrderRequest(stop_price=new_stop_loss)
                    print(f"\nRe-entering with Take profift at:{new_take_profit} and Stop loss at: {new_stop_loss}")
                    update_position(old_take=current_take_profit, 
                                    new_take=take_profit_update,
                                    old_stop=current_stop_loss, 
                                    new_stop_loss =stop_loss_update)
                    print("Position updated correclty")
                    current_stop_loss = new_stop_loss
                    current_take_profit = new_take_profit

                

        
        elif prediction == 2 and has_position:
            

            print("\n Sell signal, as we do have a position.")
            print(f"\nAttempting to close at price:")
            close_position()
            has_position = False
            is_long = False
            print("\nPosition closed succesfully")
      

   # drop the first row and ensures bars always maintains exactly 50 rows.
   #bars = df.iloc[1:].reset_index(drop=True)
   bars = df.tail(50).reset_index(drop=True)




# Streaming real data
stream = CryptoDataStream(api_key, api_secret)

'''
stream = StockDataStream(api_key,api_secret)
'''

print("Ready to run")
stream.subscribe_bars(on_new_bar, 
                        ticker)
# 1 minute bars
stream.run()


'''
- RSI: 14 days back 
- Test slow
- Few trades

-  strategy 1m timeframe
-  test with data >09/2024
'''