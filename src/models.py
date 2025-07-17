# models.py
import mlflow
import numpy as np
import pandas as pd
from typing import List, Tuple
from catboost import CatBoostRegressor
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import root_mean_squared_error
from config_schemas.TrainConfig import TrainConfig


class PriceModel:
    def __init__(self, cfg: TrainConfig):
        self.cfg = cfg
        self.model = CatBoostRegressor(
            loss_function="MAE",
            iterations=cfg.n_iter,
            depth=cfg.depth,
            learning_rate=cfg.lr,
            early_stopping_rounds=cfg.early_stop,
            random_seed=cfg.random_state,
        )

    # ---------- helpers -------------------------------------------------
    @staticmethod
    def _make_price_band(y: pd.Series) -> pd.Series:
        return pd.cut(
            y,
            bins=[0, 5e5, 1e6, 2e6, 3e6, np.inf],
            labels=[1, 2, 3, 4, 5],
        )

    def _train_test_split(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        y_band = self._make_price_band(df["price"])
        sss = StratifiedShuffleSplit(
            n_splits=1, test_size=self.cfg.test_size, random_state=self.cfg.random_state
        )
        train_idx, test_idx = next(sss.split(df, y_band))
        return df.iloc[train_idx].copy(), df.iloc[test_idx].copy()

    # ---------- public API ---------------------------------------------
    def fit(self, df: pd.DataFrame):
        train, test = self._train_test_split(df)

        X_train = train.drop(columns="price")
        y_train = train["price"].clip(
            upper=train["price"].quantile(self.cfg.clip_target_q)
        )

        if self.cfg.log_target:
            y_train = np.log1p(y_train)

        mlflow.autolog()
        self.model.fit(X_train, y_train, cat_features=self.cfg.cat_features)

        # evaluation
        y_true, y_pred = self.predict(test)
        rmse = root_mean_squared_error(y_true, y_pred)
        mlflow.log_metric("rmse", rmse)

    def predict(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        X = df.drop(columns="price")
        y_true = np.asarray(df["price"].values)
        y_pred = self.model.predict(X)
        if self.cfg.log_target:
            y_pred = np.expm1(y_pred)
        y_pred = np.asarray(y_pred)
        return y_true, y_pred
