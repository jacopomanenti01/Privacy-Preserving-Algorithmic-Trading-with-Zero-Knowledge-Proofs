import pandas as pd
import talib

def generate_features(data):
    # Add technical indicators as features
    # RSI
    data['RSI14'] = talib.RSI(data['Close'], timeperiod=14)
    data['RSI16'] = talib.RSI(data['Close'], timeperiod=16)
    data['ATR'] = talib.ATR(data['High'],data['Low'],data['Close'], timeperiod = 3)
    data['SMA_20'] = talib.SMA(data['Close'], timeperiod=20)
    data['SMA_50'] = talib.SMA(data['Close'], timeperiod=50)
    data['Bollinger_Upper'], data['Bollinger_Middle'], data['Bollinger_Lower'] = talib.BBANDS(data['Close'], timeperiod=20)
    data['ADX'] = talib.ADX(data['High'], data['Low'], data['Close'], timeperiod=14)
    data['EMA_12'] = talib.EMA(data['Close'], timeperiod=12)
    data['EMA_26'] = talib.EMA(data['Close'], timeperiod=26)
    data['MOM'] = talib.MOM(data['Close'], timeperiod=10)
    # Lagged returns as features
    #data['Return'] = data['Close'].pct_change()
    #data['Lag1'] = data['Close'].shift(1)
    #data['Lag2'] = data['Close'].shift(2)

    # Drop NaN rows
    data = data.dropna()

    return data
