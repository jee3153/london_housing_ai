# models.py
import mlflow
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from typing import Tuple, Any
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
        """
        Returns labeled series with indices of price column and the labelled price band that is based on bins.
        """
        return pd.cut(
            y,
            bins=[0, 5e5, 1e6, 2e6, 3e6, np.inf],
            labels=[1, 2, 3, 4, 5],
        )

    def _train_test_split(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        testset_ratio = self.cfg.test_size
        valset_ratio = self.cfg.val_size
        trainset_ratio = 1 - testset_ratio

        y_band = self._make_price_band(df["price"])
        train_test_splitter = StratifiedShuffleSplit(
            n_splits=1, test_size=testset_ratio, random_state=self.cfg.random_state
        )
        # split into train and test sets
        train_val_idx, test_idx = next(train_test_splitter.split(df, y_band))

        # split train sets further to train set and validation set
        train_val_df = df.iloc[train_val_idx]  # train_val features
        y_band_train_val = y_band.iloc[train_val_idx]  # train_val labels

        train_val_splitter = StratifiedShuffleSplit(
            n_splits=1,
            test_size=valset_ratio / trainset_ratio,
            random_state=self.cfg.random_state,
        )
        train_idx, val_idx = next(
            train_val_splitter.split(train_val_df, y_band_train_val)
        )

        return (
            train_val_df.iloc[train_idx].copy(),
            df.iloc[test_idx].copy(),
            train_val_df.iloc[val_idx].copy(),
        )

    # ---------- public API ---------------------------------------------
    def fit(self, df: pd.DataFrame, checksum: str):
        train, test, val = self._train_test_split(df)

        # train set
        X_train, y_train = self._split_feature_and_label(train, self.cfg.label)
        # validation set
        X_val, y_val = self._split_feature_and_label(val, self.cfg.label)

        mlflow.autolog()
        self.model.fit(
            X_train,
            y_train,
            cat_features=self.cfg.cat_features,
            eval_set=(X_val, y_val),
        )

        # test set evaluation
        y_true, y_pred = self.predict(test)
        rmse = root_mean_squared_error(y_true, y_pred)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_param("raw_csv_sha256", checksum)

        # validation set evaluation
        y_val_true, y_val_pred = self.predict(val)
        val_rmse = root_mean_squared_error(y_true, y_pred)
        mlflow.log_metric("val_rmse", val_rmse)

    def predict(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        X = df.drop(columns="price")
        y_true = np.asarray(df["price"].values)
        y_pred = self.model.predict(X)
        if self.cfg.log_target:
            y_pred = np.expm1(y_pred)
        y_pred = np.asarray(y_pred)
        return y_true, y_pred

    def _split_feature_and_label(
        self, df: pd.DataFrame, feature_col: str
    ) -> Tuple[pd.DataFrame, pd.Series | NDArray[Any]]:
        features = df.drop(columns=feature_col)
        # clipping: if the value > threshold, value = threshold to avoid outliers
        labels = df[feature_col].clip(
            upper=df[feature_col].quantile(self.cfg.clip_target_q)
        )
        if self.cfg.log_target:
            labels = np.log1p(labels)
        return features, labels
