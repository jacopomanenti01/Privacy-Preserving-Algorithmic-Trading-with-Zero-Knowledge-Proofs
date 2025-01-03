import talib
import pandas as pd

def features_extraction(data):
    
    price = data['close'].iloc[-1]
    # Skip until we have enough data for all indicators
    lookback = max(50, 20, 14, 12, 10)  # max of all your timeperiods
    if len(data['close']) < lookback:
            print("too few")
            return
    # Extract features for the current time step
    features = {
    'RSI14': talib.RSI(data['close'], timeperiod=14).iloc[-1],
    'RSI16': talib.RSI(data['close'], timeperiod=16).iloc[-1], 
    'SMA_20': talib.SMA(data['close'], timeperiod=20).iloc[-1],
    'SMA_50': talib.SMA(data['close'], timeperiod=50).iloc[-1],
    'Bollinger_Upper': talib.BBANDS(data['close'], timeperiod=20)[0].iloc[-1],
    'Bollinger_Lower': talib.BBANDS(data['close'], timeperiod=20)[2].iloc[-1],
    'ATR': talib.ATR(data['high'], data['low'], data['close'], timeperiod=3).iloc[-1],
    'ADX': talib.ADX(data['high'], data['low'], data['close'], timeperiod=14).iloc[-1],
    'EMA_12': talib.EMA(data['close'], timeperiod=12).iloc[-1],
    'EMA_26': talib.EMA(data['close'], timeperiod=26).iloc[-1],
    'MOM': talib.MOM(data['close'], timeperiod=10).iloc[-1]
    }

    # Convert and reorder
    features_df = pd.DataFrame([features])

    if features_df.isna().any().any():
        print("WARNING: NaN values detected!")
        return
    
    return features_df