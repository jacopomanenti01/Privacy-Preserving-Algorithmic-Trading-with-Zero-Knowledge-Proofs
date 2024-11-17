import pandas as pd
import talib

def generate_features(data):
    # Add technical indicators as features
    data['RSI'] = talib.RSI(data['Close'], timeperiod=14)
    data['SMA_20'] = talib.SMA(data['Close'], timeperiod=20)
    data['SMA_50'] = talib.SMA(data['Close'], timeperiod=50)
    data['Bollinger_Upper'], data['Bollinger_Middle'], data['Bollinger_Lower'] = talib.BBANDS(data['Close'], timeperiod=20)

    # Lagged returns as features
    data['Return'] = data['Close'].pct_change()
    data['Lag1'] = data['Close'].shift(1)
    data['Lag2'] = data['Close'].shift(2)

    # Drop NaN rows
    data = data.dropna()

    return data
