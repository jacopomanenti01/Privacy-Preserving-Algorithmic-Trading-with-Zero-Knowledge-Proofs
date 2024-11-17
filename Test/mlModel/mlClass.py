from backtesting import Strategy
import talib
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from .featureGenerator import generate_features
from .mlBase import model

class MLBasedStrategy(Strategy):
    upper_bound = 60
    lower_bound = 40 
    time_window = 14
    tp_perc = .10
    sl_perc = .04

    def init(self):

        # Load the pre-trained model
        self.model = model

        # Feature initialization (RSI signal)
        self.RSI_signal = self.I(talib.RSI, self.data.Close, self.time_window)

    def next(self):
        price = self.data.Close[-1]
        
        # Extract features for the current time step
        features = {
            'RSI': self.RSI_signal[-1],
            'SMA_20': talib.SMA(self.data.Close, timeperiod=20)[-1],
            'SMA_50': talib.SMA(self.data.Close, timeperiod=50)[-1],
            'Bollinger_Upper': talib.BBANDS(self.data.Close, timeperiod=20)[0][-1],
            'Bollinger_Lower': talib.BBANDS(self.data.Close, timeperiod=20)[2][-1],
            'Return': self.data.Close.pct_change()[-1],
            'Lag1': self.data.Close[-2],
            'Lag2': self.data.Close[-3]
        }

        # Convert features to dataframe-like format
        features_df = pd.DataFrame([features])

        # Get prediction (1 = Buy, 0 = Sell)
        prediction = self.model.predict(features_df)[0]

        if prediction == 1:  # Buy Signal
            if not self.position:
                stop_loss_price = price * (1 - self.sl_perc)
                take_profit_price = price * (1 + self.tp_perc)

                self.buy(size=.1, sl=stop_loss_price, tp=take_profit_price)
                print(f"ML Model predicts Buy at {price:.2f}")
        else:  # Sell Signal or Hold
            if self.position:
                print(f"ML Model predicts Sell at {price:.2f}")
                self.position.close()
