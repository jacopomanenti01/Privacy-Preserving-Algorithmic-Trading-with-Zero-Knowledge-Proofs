import pandas as pd
from sklearn.model_selection import train_test_split
from featureGenerator import generate_features
from sklearn.metrics import classification_report
import yfinance as yf
from datetime import datetime
import numpy as np
from xgboost import XGBClassifier
from sklearn.utils import class_weight
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import make_scorer, precision_score
import pickle






# Load and preprocess historical data
#data = pd.read_csv('sp500.csv')  # Replace with the correct path



sp500 = yf.Ticker("^SPX") # create a ticker symbol
date_format = '%Y-%m-%d'
end_date =  datetime.strptime("2024-09-30", date_format)
data = sp500.history(start ="2000-01-01" , end = end_date, interval = "1d")


data = generate_features(data)  # Generate features for the dataset

# Define features and target
data["Log"] = np.log(data['Close']/data['Close'].shift(1)).dropna()
X = data[['RSI14',
          'RSI16', 
          'SMA_20', 
          'SMA_50', 
          'Bollinger_Upper', 
          'Bollinger_Lower', 
          'ATR','ADX', 'EMA_12', 'EMA_26','MOM']]
#y = (data['Return'].shift(-1) > 0).astype(int)  # 1 for Buy, 0 for Sell

print(X.head())
# paramenter that can be used to optimize the ROC curve

data.fillna(0, inplace=True)
descr = data["Log"].describe()



m_log = descr["mean"]
std_log = descr["std"]

up_tresh = m_log + std_log
down_tresh = m_log - std_log


# Stationary
y = pd.Series(np.where(data["Log"] > up_tresh, 1,np.where(data["Log"] < down_tresh, 2, 0)))

print(y.value_counts())


# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify= y)

print("Training set distribution:")
print(y_train.value_counts(normalize=True))
print("\nTest set distribution:")
print(y_test.value_counts(normalize=True))

# Train a Decision Tree Classifier
#model = DecisionTreeClassifier()
sample_weight=class_weight.compute_sample_weight(
    class_weight='balanced',
    y=y_train)

model = XGBClassifier(

    learning_rate=0.1,
    max_depth=5,
    n_estimators=100
)

# Cross validation with custom scorer for weighted precision

param_grid = {
   'learning_rate': [0.01, 0.1, 0.001],
   'max_depth': [3, 5, 7, 10],
   'n_estimators': [50, 100, 200, 500, 1000],
   'min_child_weight': [1, 3, 5, 7, 10],
   'gamma': [0, 0.1, 0.2, 0.01]
}

# avoid non zero division
precision_scorer = make_scorer(precision_score, average='macro', zero_division=0)


grid_search = RandomizedSearchCV(
   estimator=XGBClassifier(),
   param_distributions=param_grid,
   cv=5,
   scoring=precision_scorer,
   n_jobs=-1
)

grid_search.fit(X_train, y_train, sample_weight=sample_weight)
print("Best parameters:", grid_search.best_params_)
print("Best score:", grid_search.best_score_)

best_model = grid_search.best_estimator_


# Pred
preds = best_model.predict(X_test)
report = classification_report(preds, y_test)
print(report)

print("Model training completed.")

print("Saving model...")
with open('binary_classifier.pkl', 'wb') as file:
    pickle.dump(best_model, file)

print("Model saved")