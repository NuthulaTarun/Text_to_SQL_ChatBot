import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from google.cloud import bigquery
from google.oauth2 import service_account
# from prophet import Prophet
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error

#bigquery connection
credentials = service_account.Credentials.from_service_account_file('credentials.json')
client = bigquery.Client(credentials=credentials, project=credentials.project_id)


#arima
def process_and_fit_model_arima(start_date, forecast_start_date,forecast_end_date,arima_order=(1, 1, 1)):
    try:
        query = f"""
        SELECT date, sum(totalTransactionRevenue) as totalTransactionRevenue
        FROM `rag-exploration-417710.cleaned_marketing_data.cleaned_public_events_data` 
        WHERE date >= '{start_date}' group by date;
        """
        data = client.query(query).to_dataframe()

        filtered_data = data[data['date'] >= pd.to_datetime(start_date)]
        grouped_data = filtered_data.groupby('date').sum()
        grouped_data.index = pd.to_datetime(grouped_data.index)
        date_range = pd.date_range(start=grouped_data.index.min(), end=grouped_data.index.max())
        data_reindexed = grouped_data.reindex(date_range)
        data_reindexed['totalTransactionRevenue'] = data_reindexed['totalTransactionRevenue'].rolling(window=3, min_periods=1).mean()
        data_index = data_reindexed.reset_index()
        data_index.rename(columns={'index': 'date'}, inplace=True)
        data_index.set_index('date', inplace=True)

        model = ARIMA(data_index['totalTransactionRevenue'], order=arima_order)
        model_fit = model.fit()

        forecast_index = pd.date_range(start=forecast_start_date, end=forecast_end_date)
        forecast = model_fit.forecast(steps=len(forecast_index))
        forecast_df = pd.DataFrame({'date': forecast_index, 'forecast_totalTransactionRevenue': forecast})
        forecast_df.set_index('date', inplace=True)
        data_with_predictions = pd.concat([data_index, forecast_df], axis=1)
        print(data_with_predictions)
        return data_with_predictions

        #return data_index, model_fit
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

# #prophet
# def process_and_prepare_data_prophet(start_date,forecast_start_date,forecast_end_date):
#     try:
#         query = f"""
#         SELECT date, sum(totalTransactionRevenue) as totalTransactionRevenue
#         FROM `rag-exploration-417710.cleaned_marketing_data.cleaned_public_events_data` 
#         WHERE date >= '{start_date}' group by date;
#         """
#         data = client.query(query).to_dataframe()
#         filtered_data = data[data['date'] >= pd.to_datetime(start_date)]
#         grouped_data = filtered_data.groupby('date').sum()
#         grouped_data.index = pd.to_datetime(grouped_data.index)
#         date_range = pd.date_range(start=grouped_data.index.min(), end=grouped_data.index.max())
#         data_reindexed = grouped_data.reindex(date_range)
#         data_reindexed['totalTransactionRevenue'] = data_reindexed['totalTransactionRevenue'].rolling(window=3, min_periods=1).mean()
#         data_reindexed['totalTransactionRevenue'].fillna(data_reindexed['totalTransactionRevenue'].mean(), inplace=True)
#         data_index = data_reindexed.reset_index()
#         data_index.rename(columns={'index': 'date'}, inplace=True)
#         data_index.rename(columns={'date': 'ds', 'totalTransactionRevenue': 'y'}, inplace=True)
#         model = Prophet()
#         model.fit(data_index)
#         future_dates = pd.date_range(start=forecast_start_date, end=forecast_end_date)
#         future_df = pd.DataFrame({'ds': future_dates})
#         forecast = model.predict(future_df)
#         fig, ax = plt.subplots(figsize=(12, 6))
#         model.plot(forecast, ax=ax)
#         # plt.title('Prophet Forecast with Predictions')
#         # plt.xlabel('Date')
#         # plt.ylabel('Total Transaction Revenue')
#         # plt.show()

#         data_with_predictions = pd.concat([data_index.set_index('ds'), forecast.set_index('ds')[['yhat']]], axis=1)
#         print(data_with_predictions)
#         data_with_predictions.to_excel('Prophet_output.xlsx')
#         return data_with_predictions
#         #return data_index
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         raise


#random Forest
def process_and_prepare_data_random_forest(start_date, forecast_start_date, forecast_end_date, feature):
    feature_list = ['revenue', 'hits', 'pageviews', 'session_time']
    
    if feature not in feature_list:
        raise ValueError(f"Feature '{feature}' is not in the allowed list: {feature_list}")
    
    try:
        # Define the SQL query based on the selected feature
        if feature == 'revenue':
            query = f"""
            SELECT date, SUM(totalTransactionRevenue) as revenue
            FROM `rag-exploration-417710.cleaned_marketing_data.cleaned_public_events_data` 
            WHERE date >= '{start_date}' 
            GROUP BY date;
            """
        
        elif feature == 'hits':
            query = f"""
            SELECT date, SUM(hits_totals) as hits
            FROM `rag-exploration-417710.cleaned_marketing_data.cleaned_public_events_data` 
            WHERE date >= '{start_date}' 
            GROUP BY date;
            """
        
        elif feature == 'pageviews':
            query = f"""
            SELECT date, SUM(pageviews) as pageviews
            FROM `rag-exploration-417710.cleaned_marketing_data.cleaned_public_events_data` 
            WHERE date >= '{start_date}' 
            GROUP BY date;
            """
        
        elif feature == 'session_time':
            query = f"""
            SELECT date, SUM(session_time) as session_time
            FROM `rag-exploration-417710.cleaned_marketing_data.cleaned_public_events_data` 
            WHERE date >= '{start_date}' 
            GROUP BY date;
            """
        
        # Fetch the data using the dynamically constructed query
        data = client.query(query).to_dataframe()
        filtered_data = data[data['date'] >= pd.to_datetime(start_date)]
        
        # Grouping the data by date
        grouped_data = filtered_data.groupby('date').sum()
        grouped_data.index = pd.to_datetime(grouped_data.index)
        date_range = pd.date_range(start=grouped_data.index.min(), end=grouped_data.index.max())
        data_reindexed = grouped_data.reindex(date_range)
        
        # Handling null values
        data_reindexed[feature] = data_reindexed[feature].fillna(method='bfill')
        data_index = data_reindexed.reset_index()
        data_index.rename(columns={'index': 'date'}, inplace=True)
        
        # creating additional features
        data_index['year'] = data_index['date'].dt.year
        data_index['month'] = data_index['date'].dt.month
        data_index['day'] = data_index['date'].dt.day
        data_index['dayofweek'] = data_index['date'].dt.dayofweek
        
        data_1 = data_index.copy()
        
        for lag in range(1, 8):
            data_index[f'lag_{lag}'] = data_index[feature].shift(lag)

        data_index.dropna(inplace=True)
        print(data_index.columns)
        print(f"Prepared data for Random Forest with shape: {data_index.shape}")
        
        # Calculate the number of samples for training (80%) and testing (20%)
        train_size = int(len(data_index) * 0.8)
        test_size = len(data_index) - train_size

        # Split the DataFrame into training and testing sets
        train_data = data_index.iloc[:train_size]
        test_data = data_index.iloc[train_size:]
        print(f"Train data shape: {train_data.shape}")
        print(f"Test data shape: {test_data.shape}")
        
        # Training
        features = train_data.drop(['date', feature, 'year', 'dayofweek', 'lag_4', 'lag_5', 'lag_6', 'lag_7'], axis=1)
        target = train_data[feature]
        print(f"Training data features shape: {features.shape}")
        print(f"Training data target shape: {target.shape}")
        
        if features.empty or target.empty:
            raise ValueError("Training data is empty. Check data preparation steps.")
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(features, target)

        # Convert date strings to the correct format
        future_dates = pd.date_range(start=forecast_start_date,
                            end=forecast_end_date)
        future_df = pd.DataFrame({'date': future_dates})
        future_df['year'] = future_df['date'].dt.year
        future_df['month'] = future_df['date'].dt.month
        future_df['day'] = future_df['date'].dt.day
        future_df['dayofweek'] = future_df['date'].dt.dayofweek
        
        # concatenating future df and data_index
        data_index = pd.concat([data_index, future_df], ignore_index=True)
        
        # creating forecasted_value column and assigning null values to it.
        data_index["forecasted_value"]= np.nan

        # code to calcuate the inference
        for date_value in future_dates:
            print(f'date_value is {date_value}')
            for lag in range(1, 8):
                data_index[f'lag_{lag}'] = data_index[feature].shift(lag)
            df_select = data_index[data_index["date"] == date_value]
            df_select = df_select.fillna(0)
            df_inference = df_select[['month', 'day', 'lag_1','lag_2','lag_3']]
            future_forecast = model.predict(df_inference)

            # Convert future_forecast to the correct dtype if necessary
            future_forecast = np.array(future_forecast).astype(np.float64)
            
            # Ensure feature column is float64 before assignment
            data_index[feature] = data_index[feature].astype(np.float64)
            data_index['forecasted_value'] = data_index['forecasted_value'].astype(np.float64) 

            # Assigning forecast value to feature column and forecasted value column.
            data_index.loc[data_index['date'] == date_value, feature] = future_forecast[0]
            data_index.loc[data_index['date'] == date_value, 'forecasted_value'] = future_forecast[0]
        
        # Making feature column values null for future dates
        data_index.loc[data_index['date'] >= future_dates[0], feature] = np.nan
        
        # selecting columns
        data_with_predictions = data_index[["date",feature,"forecasted_value"]]
        
        return data_with_predictions
    except Exception as e:
        print(f"An error occurred: {e}")
        raise


def run_model(model_name, start_date, forecast_start_date, forecast_end_date,feature):
    if model_name == 'arima':
        results = process_and_fit_model_arima(start_date, forecast_start_date,forecast_end_date,arima_order=(1, 1, 1))
    elif model_name == 'random_forest':
        results = process_and_prepare_data_random_forest(start_date,forecast_start_date,forecast_end_date,feature)
        return results
    else:
        raise ValueError(f"Model {model_name} is not supported.")
    return results



def get_forecasting_results(model_name,start_date,forecast_start_date,forecast_end_date,feature):  
    model_results = run_model(model_name, start_date, forecast_start_date, forecast_end_date,feature)
    return model_results

def process_forecast_results(model_results, feature):
    model_results = model_results.reset_index(drop=True)
    
    model_results["date"] = pd.to_datetime(model_results["date"])
    forecast_start_date_4_weeks_before = datetime.date.today() - datetime.timedelta(
        weeks=4
    )
    forecast_start_date_4_weeks_before = forecast_start_date_4_weeks_before.strftime(
        "%Y-%m-%d"
    )
    
    # Filtering only last 4 weeks results
    model_results = model_results[
        (model_results["date"] >= pd.Timestamp(forecast_start_date_4_weeks_before))
    ].reset_index(drop=True)
    

    # for loop to get last value of the actual transaction
    for i in range(1, 30):
        # Dynamically set forecast_start_date to today's date
        day_before = datetime.date.today() - datetime.timedelta(days=i)
        print(f'day_before is {day_before}')

        # Convert dates to strings if needed (e.g., for plotting or other purposes)
        day_before = day_before.strftime("%Y-%m-%d")

        # try to handle the errors.
        try:
            # get the last value of totalTransactionRevenue
            last_actual_value = model_results.loc[
                model_results["date"] == pd.Timestamp(day_before),
                feature,
            ].values[0]
            if not np.isnan(last_actual_value):
                break
        except Exception as e:
            print(f"Error: {e}")

    model_results.loc[
        model_results["date"] == pd.Timestamp(day_before),
        "forecasted_value",
    ] = last_actual_value

    # Melt the DataFrame to long format
    model_results = model_results.melt(
        id_vars="date",
        value_vars=[feature, "forecasted_value"],
        var_name="column",
        value_name="value",
    )
    model_results = model_results.reset_index(drop=True)
    return model_results
