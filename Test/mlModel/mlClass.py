from backtesting import Strategy
import talib
import pandas as pd
import joblib
import os
from backtesting.lib import crossover, TrailingStrategy


class MLBasedStrategy(Strategy):
    upper_bound = 60
    lower_bound = 40 
    time_window = 14
    tp_perc = .10
    sl_perc = .04

    def init(self):
        # Load the pre-trained model
        self.path = os.path.join(os.path.dirname(__file__), 'best_model_xboost.joblib')


        self.model = joblib.load(self.path)

        # Feature initialization (RSI signal)
        self.RSI_signal = self.I(talib.RSI, self.data.Close, self.time_window)

    def next(self):
        price = self.data.Close[-1]
        # Skip until we have enough data for all indicators
        lookback = max(50, 20, 14, 12, 10)  # max of all your timeperiods
        if len(self.data.Close) < lookback:
            print("too few")
            return
        
        # Extract features for the current time step
        features = {
   'RSI14': talib.RSI(self.data.Close, timeperiod=14)[-1],
   'RSI16': talib.RSI(self.data.Close, timeperiod=16)[-1], 
   'SMA_20': talib.SMA(self.data.Close, timeperiod=20)[-1],
   'SMA_50': talib.SMA(self.data.Close, timeperiod=50)[-1],
   'Bollinger_Upper': talib.BBANDS(self.data.Close, timeperiod=20)[0][-1],
   'Bollinger_Lower': talib.BBANDS(self.data.Close, timeperiod=20)[2][-1],
   'ATR': talib.ATR(self.data.High, self.data.Low, self.data.Close, timeperiod=3)[-1],
   'ADX': talib.ADX(self.data.High, self.data.Low, self.data.Close, timeperiod=14)[-1],
   'EMA_12': talib.EMA(self.data.Close, timeperiod=12)[-1],
   'EMA_26': talib.EMA(self.data.Close, timeperiod=26)[-1],
   'MOM': talib.MOM(self.data.Close, timeperiod=10)[-1]
}

        # Convert and reorder
        features_df = pd.DataFrame([features])

        if features_df.isna().any().any():
            print("WARNING: NaN values detected!")
            return

        # Get prediction (1 = Buy, 2 = Sell, 0 = stationary)
        prediction = self.model.predict(features_df)[0]

        # OVERSOLD condition - ENTER LONG
        if crossover(self.lower_bound, self.RSI_signal):
            print("OVERSOLD SIGNAL DETECTED!")
            print(f"prediction: {prediction}")
            print(f"Do I have a position? {self.position}")

            if prediction == 1:  # Buy Signal


                if not self.position:
                    print("Buying")
                    # Calculate stop loss and take profit prices
                    stop_loss_price = price * (1 - self.sl_perc)
                    take_profit_price = price * (1 + self.tp_perc)
                    
                    print(f"Attempting to buy at {price}")
                    print(f"Stop Loss: {stop_loss_price}")
                    print(f"Take Profit: {take_profit_price}")
                    
                    # Buy with explicit size and SL/TP levels
                    #order = self.buy(size=.1, sl=stop_loss_price, tp=take_profit_price)
                    order = self.buy(
                            size=0.1, 
                            sl=stop_loss_price, 
                            tp=take_profit_price,
                            limit=price  # Add limit price
                        )
                    print(f"Order result: {order}")
                    print(f"Position after order: {self.position}")


                # Close any existing position first
                else:
                    print("Keeping position in up situation and oversold signal" )
                    print(f"Current position P/L: {self.position.pl_pct:.2%}")
                    
                    if self.position.pl_pct >= 0.03:  # Changed from 0.5 to 0.05 (5%)
                        print("Position profit >= 3%, closing and re-entering")
                        self.position.close()
                        
                        new_stop_loss_price = price * (1 - self.sl_perc)
                        new_take_profit_price = price * (1 + self.tp_perc)
                        
                        # Buy with explicit size and SL/TP levels
                        #order = self.buy(size=.1, sl=new_stop_loss_price, tp=new_take_profit_price)
                        order = self.buy(
                            size=0.1, 
                            sl=stop_loss_price, 
                            tp=take_profit_price,
                            limit=price  # Add limit price
                        )
                        print(f"Re-entry order result: {order}")
                        print(f"Position after order: {self.position}")

                        
            elif prediction == 0:  # Stationary Signal
                
    
                # Close any existing position first
                if self.position:
                    print("Keeping position in stationary situation and oversold signal")

            else: 
                if self.position:
                    print("Closing existing position in down situation and oversold signal")
                    self.position.close()

        elif crossover(self.RSI_signal, self.upper_bound):
            print("OVERBOUGHT SIGNAL DETECTED!")
            print(f"prediction: {prediction}")
            print(f"Do I have a position? {self.position}")




            if prediction == 1:  # Buy Signal
                    
                if self.position:
                    print(f"Current position P/L: {self.position.pl_pct:.2%}")
                    
                    if self.position.pl_pct >= 0.03:  # Changed from 0.5 to 0.05 (5%)
                        print("Position profit >= 3%, closing and re-entering")
                        self.position.close()
                        
                        new_stop_loss_price = price * (1 - self.sl_perc)
                        new_take_profit_price = price * (1 + self.tp_perc)
                        
                        # Buy with explicit size and SL/TP levels
                        #order = self.buy(size=.1, sl=new_stop_loss_price, tp=new_take_profit_price)
                        order = self.buy(
                            size=0.1, 
                            sl=stop_loss_price, 
                            tp=take_profit_price,
                            limit=price  # Add limit price
                        )
                        print(f"Re-entry order result: {order}")
                        print(f"Position after order: {self.position}")


            elif prediction == 0:
                 if self.position:
                    print(f"Current position P/L: {self.position.pl_pct:.2%}")


            else:
                if self.position:
                    print("Closing existing position")
                    self.position.close()
            