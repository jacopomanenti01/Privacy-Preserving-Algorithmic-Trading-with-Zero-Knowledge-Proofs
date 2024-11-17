import pandas as pd
import talib
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from featureGenerator import generate_features

# Load and preprocess historical data
data = pd.read_csv('sp500.csv')  # Replace with the correct path
data = generate_features(data)  # Generate features for the dataset

# Define features and target
X = data[['RSI', 'SMA_20', 'SMA_50', 'Bollinger_Upper', 'Bollinger_Lower', 'Return', 'Lag1', 'Lag2']]
y = (data['Return'].shift(-1) > 0).astype(int)  # 1 for Buy, 0 for Sell

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# Train a Decision Tree Classifier
model = DecisionTreeClassifier()
model.fit(X_train, y_train)

print("Model training completed.")
