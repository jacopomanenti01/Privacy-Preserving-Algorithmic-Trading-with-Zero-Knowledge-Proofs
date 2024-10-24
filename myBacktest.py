from backtesting import Backtest, Strategy
from backtesting.lib import crossover, TrailingStrategy
import talib

class FirstStrategy(Strategy):

    upper_bound = 60
    lower_bound = 40 
    time_window = 14
    tp_perc = .05
    sl_perc = .10

    def init(self):
        self.RSI_signal = self.I(talib.RSI,self.data.Close,self.time_window  )

    def next(self):

        # current price
        price = self.data.Close[-1]

        if self.position: # as we do not allow for short positions
            if crossover(self.RSI_signal, self.upper_bound):
                if self.position.pl_pct>=.1:
                    self.position.close()
                    new_stop_loss_price = price * (1 - self.sl_perc)
                    new_take_profit_price = price * (1 + self.tp_perc)

                    # Update the position with new stop loss and take profit
                    if new_stop_loss_price > 0 and new_take_profit_price > new_stop_loss_price:
                        self.buy(sl=new_stop_loss_price, tp=new_take_profit_price)

                elif crossover(self.RSI_signal, self.upper_bound) and self.position.pl_pct<.1:
                    # overbought 
                    self.position.close()

        elif crossover(self.lower_bound, self.RSI_signal):
            # oversold, long position
            if self.position:
               self.position.close() 
            else:
                # Calculate stop loss and take profit based on the entry price
                stop_loss_price = price * (1 - self.sl_perc)
                take_profit_price = price * (1 + self.tp_perc)


                # oversold, no position, buy 10% of total cash remaining
                self.buy(tp = take_profit_price, sl= stop_loss_price)



