from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, StopLossRequest, TakeProfitRequest, ReplaceOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass, QueryOrderStatus
from alpaca.data.live import StockDataStream
from alpaca.trading.requests import GetOrdersRequest
from alpaca.common.exceptions import APIError



import pandas as pd
from dotenv import load_dotenv
import talib
import os
import joblib
import asyncio



# Internal Imports
from utils.feature import features_extraction
from utils.prediction import trend_classification
from utils.historical_bars import GetHistoricalBars

from database.influxdb import (get_influx_client,
    write_throughput,
    close_throughput)




class TradingBot():
    def __init__(self,
                 ticker, 
                 api_key,api_secret, 
                 OVERBOUGHT_THRESH, 
                 OVERSOLD_THRESH, 
                 PERC_THRESH,
                 tp_perc, 
                 sl_perc,
                 model_path,
                 delta):
        
        self.ticker = ticker
        self.trading_client = TradingClient(api_key, api_secret)
        self.OVERBOUGHT_THRESH = OVERBOUGHT_THRESH
        self.OVERSOLD_THRESH = OVERSOLD_THRESH
        self.PERC_THRESH = PERC_THRESH

        self.tp_perc = tp_perc
        self.sl_perc = sl_perc

        self.model = joblib.load(model_path)

        self.has_position =  False    # can I use directly the function?

        self.current_stop_loss= None
        self.current_take_profit = None

        self.price = None

        self.data = None

        self.broker = GetHistoricalBars(ticker,api_key, api_secret)

        self.delta = delta

        self.streamer = StockDataStream(api_key,api_secret)


        # need to set
        self.influx_client = None
        self.influx_write_api = None



    def initialize_data(self):
        self.data = self.broker.retreive_historical_bars(self.delta)
        
    async def init_influx_db(self):
        self.influx_client = await get_influx_client()
        self.influx_write_api = self.influx_client.write_api()

    def check_has_position(self):
        positions = self.trading_client.get_all_positions()
        self.has_position = len(positions) > 0 
        if self.has_position:
            print("You have already a position")
        else:
            print("You don't have a position yet")
        
    # helper function for placing the market order
    def place_market_order(self, side,price):

        stop_loss = round(price*(1 - self.sl_perc),2)
        # set limit price 0.5% below stop price 
        take_profit = round(price*(1 + self.tp_perc),2)

        if side == OrderSide.BUY:
            if not (stop_loss < price < take_profit):
                raise ValueError("Invalid price levels for BUY order")
        elif side == OrderSide.SELL:
            if not (take_profit < price < stop_loss):
                raise ValueError("Invalid price levels for SELL order")



        print(f"Price:{price}, \n Take: {take_profit}, \n Stop: {stop_loss}")
        stop_loss = StopLossRequest(stop_price = stop_loss)
        
        take_profit = TakeProfitRequest(limit_price=take_profit)

        order_data = MarketOrderRequest(
            symbol = self.ticker,
            qty = 1,
            side = side,
            order_class = OrderClass.BRACKET, 
            time_in_force = TimeInForce.GTC,
            take_profit = take_profit,
            stop_loss = stop_loss
        )


        return self.trading_client.submit_order(order_data)

    def close_position(self):
        self.has_position = False
        return self.trading_client.close_all_positions(True)
    
    def get_pl_client(self):
        pos_info = self.trading_client.get_all_positions()[0]
        plpc = float(pos_info.unrealized_plpc)*100
        return plpc

    def update_position(self, new_take, new_stop):
        print(f"updating take id:{self.current_take_profit.id} stop loss id:{self.current_stop_loss.id}")
        new_take_profit = self.trading_client.replace_order_by_id(self.current_take_profit.id, new_take)
        new_stop_loss = self.trading_client.replace_order_by_id(self.current_stop_loss.id, new_stop)
        return new_take_profit, new_stop_loss

    def buy_bracket(self): 
        # place order
        parent_order = self.place_market_order(OrderSide.BUY, self.price)
        # set current take/stop
        current_take_profit = parent_order.legs[0]
        current_stop_loss = parent_order.legs[1]

        # set flags
        self.has_position = True
        self.current_stop_loss = current_stop_loss
        self.current_take_profit = current_take_profit



        print(f"\nOrder placed succesfully: {parent_order}.")
        return parent_order

    def retrieve_brackets(self):
        # get all open positions
        get_orders_data = GetOrdersRequest(
            status=QueryOrderStatus.ALL,
            limit=3,
            nested=True  # show nested multi-leg orders
        )

        # filter position by ticker
        ticker_arr = self.trading_client.get_orders(filter=get_orders_data)
        print(ticker_arr)

        is_last_bracket = True
        for item in ticker_arr:
            if item.replaces !=None:
                is_last_bracket = False

        if is_last_bracket:
            # means that the last 3 orders were a bracket order
            self.current_take_profit = ticker_arr[0].legs[0]
            self.current_stop_loss = ticker_arr[0].legs[1]
        else:
            # means that the last 3 orders were take/profit updates
            self.current_stop_loss  = ticker_arr[0]
            self.current_take_profit = ticker_arr[1]

    def update_bracket(self):

        if self.current_take_profit is None and self.current_stop_loss is None:
            print("Retrieving last take profit and stop loss")
            self.retrieve_brackets()
            

        # get current return
        plpc = self.get_pl_client()

        print(f"\nCurrent position plpc: {plpc}")

        if plpc >= self.PERC_THRESH:
            print(f"\n updating position, plpc {plpc} > threshold {self.PERC_THRESH}")

            try:
                new_stop_loss =  round(self.price*(1 - self.sl_perc),2)
                new_take_profit = round(self.price*(1 + self.tp_perc),2)

                take_profit_update = ReplaceOrderRequest(limit_price=new_take_profit)
                stop_loss_update = ReplaceOrderRequest(
                    stop_price=new_stop_loss,
                    )
                
                print(f"\nRe-entering with Take profift at:{new_take_profit} and Stop loss at: {new_stop_loss}")

                new_take_profit, new_stop_loss = self.update_position( 
                    new_take=take_profit_update,
                    new_stop =stop_loss_update)
                
                print("Position updated correclty")
                print(new_take_profit)
                print(new_stop_loss)

                self.current_take_profit = new_take_profit
                self.current_stop_loss = new_stop_loss

                return (new_take_profit,new_stop_loss)

            except APIError as e:
                if "order parameters are not changed" in str(e):
                    print("Order parameters haven't changed. Skipping update.")
                elif "order is not open" in str(e):
                    print("Orders are not in an updatable state. Current status:")
                    print(f"Take profit status: {self.current_take_profit.status}")
                    print(f"Stop loss status: {self.current_stop_loss.status}")
                else:
                    print(f"Unexpected API error: {e}")

            except Exception as e:
                print(f"Unexpected error during order update: {e}")

        else:
            print(f"\n failed to update position, plpc {plpc} < threshold {self.PERC_THRESH}")
            return
    
    async def store_order(self, order, is_updated = False):
        await write_throughput(self.influx_write_api, order, self.price, is_updated)
    
    async def store_closed_position(self, order):
        await close_throughput(self.influx_write_api, order, self.price)

    # Fallback function
    async def on_new_bar(self,bar):
        #bars.append(bar)
        print("New bar!")
        bar_df = pd.DataFrame([dict(bar)])
        df = pd.concat([self.data, bar_df], ignore_index=True)

    
        if len(df)>=50: # Need at least 50 bars to calculate SMA_50 (check feature.py in utils folder)
            print(df)


            self.check_has_position()
            # Calculate Latest RSI

            rsi_value = talib.RSI(df['close'], timeperiod=14).iloc[-1]
            print(f"RSI IS {rsi_value}")

            self.price = df['close'].iloc[-1]
            print(f"Price is {self.price}")

            features = features_extraction(df)
            prediction = trend_classification(features, self.model)
            

            # Trading logic
            if rsi_value<=self.OVERSOLD_THRESH:
                print(f"\nOversold condition met: current RSI is {rsi_value}<{self.OVERSOLD_THRESH}")
                print(f"\nCurrent trend predictin is: {prediction}")

                if prediction ==1: 
                    if not self.has_position:
                        print("\nBuy signal, as we did not have a position.")
                        order = self.buy_bracket()
                        if order is not None:  # Make sure order was updated successfully
                            try:
                                await self.store_order(order=order)
                                print("Order added and stored successfully")
                            except Exception as e:
                                print(f"Failed to store updated order: {e}")

                    elif self.has_position:
                        print("\nUpdate signal, as we have already a position, rsi <oversold threshold, up-trend prediction")
                        order = self.update_bracket()
                        if order is not None:  # Make sure order was updated successfully
                            try:
                                await self.store_order(order=order, is_updated=True)
                                print("Order updated and stored successfully")
                            except Exception as e:
                                print(f"Failed to store updated order: {e}")

                elif prediction == 2 and self.has_position == True:   
                    print("\n Sell signal, as we do have a position.")
                    print(f"\nAttempting to close at price:")
                    closed_order = self.close_position()[0].body
                    if closed_order is not None:  # Make sure order was updated successfully
                            try:
                                await self.store_closed_position(order=closed_order)
                                print("Closed order added and stored successfully")
                            except Exception as e:
                                print(f"Failed to store updated order: {e}")

                    print("\nPosition closed succesfully")





            elif rsi_value>=self.OVERBOUGHT_THRESH:
                print(f"\nOverbought condition met: current RSI is {rsi_value}>={self.OVERBOUGHT_THRESH}")
                print(f"\nCurrent trend predictin is: {prediction}")

                if prediction == 1:
                    if self.has_position:
                        order = self.update_bracket()
                        if order is not None:  # Make sure order was updated successfully
                            try:
                                await self.store_order(order=order, is_updated=True)
                                print("Order updated and stored successfully")
                            except Exception as e:
                                print(f"Failed to store updated order: {e}")


                        

                
                elif prediction == 2 and self.has_position:
                    print("\n Sell signal, as we do have a position.")
                    print(f"\nAttempting to close at price:")
                    closed_order = self.close_position()[0].body
                    if closed_order is not None:  # Make sure order was updated successfully
                            try:
                                await self.store_closed_position(order=closed_order)
                                print("Closed order added and stored successfully")
                            except Exception as e:
                                print(f"Failed to store updated order: {e}")

                    print("\nPosition closed succesfully")
            

        # drop the first row and ensures bars always maintains exactly 50 rows.
        self.data = df.tail(50).reset_index(drop=True)

    async def run(self):
        self.streamer.subscribe_bars(self.on_new_bar, 
                            self.ticker)
        print("Ready to run, waiting for a new stream to come")
        

        await self.streamer._run_forever()











async def main():
    repo_root = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(repo_root, "Test", "mlModel", "best_model_xboost.joblib")
    print(f"Model in path: {path}")

    # load env variables
    load_dotenv()
    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_API_SECRET")


    # initialize trading bot
    bot = TradingBot(ticker = "AAPL", 
                 api_key=api_key,
                 api_secret=api_secret, 
                 OVERBOUGHT_THRESH=60, 
                 OVERSOLD_THRESH=40, 
                 PERC_THRESH=-500000,
                 tp_perc=.10, 
                 sl_perc=.04,
                 model_path=path,
                 delta=80)
    
    await bot.init_influx_db()
    
    # initialize data
    bot.initialize_data()

    # run the model
    await bot.run()

    # condition to stop it
    
    






        
            
if __name__ =="__main__":
    # initialize the model
    asyncio.run(main())


    
