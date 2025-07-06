import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from sklearn.model_selection import StratifiedShuffleSplit
from typing import Tuple
from catboost import CatBoostRegressor
from sklearn.metrics import root_mean_squared_error
import mlflow
import mlflow.catboost
from mlflow.models import infer_signature

class ModelTrainer:
    def __init__(self, df: DataFrame):
        self.df = df
    """
    Categorise price to split dataset in terms of the range of prices and 
    label price band between 1 - 5,
    which splits test and train sets.

    labels : ranges
        1: £0 - £500,000
        2: £500,000 - £1,000,000
        3: £1,000,000 - £2,000,000
        4: £2,000,000 - £3,000,000
    """
    def categorise_feature(self, feature_column: str) -> Series:
        categorised = self.df["price_band"] = pd.cut(
            self.df[feature_column],
            bins=[0, 500000, 1000000, 2000000, 3000000, np.inf],
            labels=[1,2,3,4,5]
        )    
        return categorised    

    """
    re-shuffle only once
    and keep 20% as a test set.
    Reason for using stratified shuffle:
    To have well distributed dataset for train, and test set across categories
    """
    def split_test_train_set(self, feature_column: str) -> Tuple[DataFrame, DataFrame]:
        price_band = self.categorise_feature(feature_column)   

        splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        # since we only iterate once, call next() to get first item from iterator
        train_index, test_index = next(splitter.split(self.df, price_band))

        # to give train/test frames their own memory to avoid mutate to those sets.
        df_train = self.df.iloc[train_index].copy()
        df_test = self.df.iloc[test_index].copy() 

        del self.df['price_band']
        del df_train['price_band']
        del df_test['price_band']  
            
        return df_train, df_test  

    def train(self):
        train_set, test_set = self.split_test_train_set("price")
        
        y_column = ["price"]
        x_columns = train_set.columns.difference(y_column)
        x_train = train_set[x_columns]
        y_train = train_set[y_column]
        
        p99 = y_train["price"].quantile(0.99)
        y_train_capped = y_train["price"].clip(upper=p99)

        categorical_features = x_train.select_dtypes(include=["object", "category"]).columns.tolist()
        print(f"Categorical columns to pass to CatBoost: {categorical_features}")

        model = CatBoostRegressor(
            loss_function="MAE",
            depth=8,
            iterations=4000,
            learning_rate=0.05,
            l2_leaf_reg=3,
            early_stopping_rounds=200,
            random_seed=42
        )

        # log-transform ONLY the target(price column) to handle right-skewed distribution, by compressing those extreme values
        # and fit a model on the logged target
        model.fit(x_train, np.log1p(y_train_capped), cat_features=categorical_features)

        y_test, y_pred = self.predict(test_set, model)
        x_test = test_set[x_columns]

        rmse = root_mean_squared_error(y_test, y_pred)
        signature = infer_signature(x_train)
        import scipy.stats as st

        price = self.df["price"]
        print("Skew:", st.skew(price), "  Kurtosis:", st.kurtosis(price, fisher=False))

        with mlflow.start_run():
            mlflow.log_param("model_type", "CatBoostRegression")
            mlflow.log_param("features", x_test.columns.tolist())
            mlflow.log_metric("rmse", rmse)
            mlflow.catboost.log_model(
                cb_model=model, 
                name="catboost_model",
                signature=signature,
                input_example=x_train.iloc[:1] # single row example
            )

        

    def predict(self, test_set: DataFrame, model: CatBoostRegressor) -> Tuple[DataFrame, DataFrame]:
        y_column = ["price"]
        x_columns = test_set.columns.difference(y_column)
        x_test = test_set[x_columns]
        y_test = test_set[y_column]
        y_pred = model.predict(x_test)

        # predict in log-space, then invert
        return y_test, np.expm1(y_pred)
        

        