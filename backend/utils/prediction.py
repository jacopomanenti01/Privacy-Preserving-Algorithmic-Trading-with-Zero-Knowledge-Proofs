
def trend_classification(features, model):
    
    # Get prediction (1 = Buy, 2 = Sell, 0 = stationary)
    prediction = model.predict(features)[0]

    return prediction