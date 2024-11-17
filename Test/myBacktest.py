from backtesting import Backtest, Strategy
from backtesting.lib import crossover, TrailingStrategy
import talib


class FirstStrategy(Strategy):

    upper_bound = 60
    lower_bound = 40 
    time_window = 14
    tp_perc = .10
    sl_perc = .04

    def init(self):
        self.RSI_signal = self.I(talib.RSI,self.data.Close,self.time_window )

    def next(self):

        # current price (which day? yesterda or today?)
        price = self.data.Close[-1]

        # Check RSI conditions and print current values
        print(f"Current RSI: {self.RSI_signal[-1]:.2f}")
        print(f"Current Price: {price:.2f}")
        
        # OVERSOLD condition - ENTER LONG
        if crossover(self.lower_bound, self.RSI_signal):
            print("OVERSOLD SIGNAL DETECTED!")
            
            # Close any existing position first
            if self.position:
                print("Closing existing position")
                self.position.close()
            
            # Calculate stop loss and take profit prices
            stop_loss_price = price * (1 - self.sl_perc)
            take_profit_price = price * (1 + self.tp_perc)
            
            print(f"Attempting to buy at {price}")
            print(f"Stop Loss: {stop_loss_price}")
            print(f"Take Profit: {take_profit_price}")
            
            # Buy with explicit size and SL/TP levels
            order = self.buy(size=.1, sl=stop_loss_price, tp=take_profit_price)
            print(f"Order result: {order}")

        # OVERBOUGHT condition - EXIT or RE-ENTER
        elif crossover(self.RSI_signal, self.upper_bound):
            print("OVERBOUGHT SIGNAL DETECTED!")
            
            if self.position:
                print(f"Current position P/L: {self.position.pl_pct:.2%}")
                
                if self.position.pl_pct >= 0.07:  # Changed from 0.5 to 0.05 (5%)
                    print("Position profit >= 5%, closing and re-entering")
                    self.position.close()
                    
                    new_stop_loss_price = price * (1 - self.sl_perc)
                    new_take_profit_price = price * (1 + self.tp_perc)
                    
                    # Buy with explicit size and SL/TP levels
                    order = self.buy(size=.1, sl=new_stop_loss_price, tp=new_take_profit_price)
                    print(f"Re-entry order result: {order}")
                else:
                    print("Position profit < 5%, closing position")
                    self.position.close()