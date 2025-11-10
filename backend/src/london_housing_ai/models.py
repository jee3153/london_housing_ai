from pathlib import Path
from typing import Any, Tuple, Union, Dict
from enum import Enum
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from numpy.typing import NDArray
from sklearn.metrics import mean_squared_error, root_mean_squared_error, r2_score
from sklearn.model_selection import StratifiedShuffleSplit

from london_housing_ai.config_schemas.TrainConfig import TrainConfig
from london_housing_ai.utils.logger import get_logger

logger = get_logger()

YType = Union[pd.Series, NDArray[np.float64]]


class MetricType(Enum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


class PriceModel:
    def __init__(self, cfg: TrainConfig):
        self.cfg = cfg
        params = {
            "loss_function": "MAE",
            "iterations": cfg.n_iter,
            "depth": cfg.depth,
            "learning_rate": cfg.lr,
            "early_stopping_rounds": cfg.early_stop,
            "random_seed": cfg.random_state,
        }
        self.model = CatBoostRegressor(**params)
        self.log_data: dict[str, Any] = {
            "params": params,
            "artifacts": [],
            "metrics": {},
            "text": {},
        }

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

    def _train_model(
        self, train_set: pd.DataFrame, validation_set: pd.DataFrame
    ) -> Tuple[YType, YType]:
        """
        Teach the model to learn patterns
        Student's practice problem:
        If models were student, they can look up solutions and learn from them.
        Model learns the relationship between input features and target labels here
        """
        # train set
        X_train, y_train = self._split_feature_and_label(train_set, self.cfg.label)
        # validation set
        X_val, y_val = self._split_feature_and_label(validation_set, self.cfg.label)

        self.model.fit(
            X_train,
            y_train,
            cat_features=self.cfg.cat_features,
            eval_set=(X_val, y_val),
        )

        y_train_true, y_train_pred = self.model.predict(train_set)

        # Feature importances
        importances = self.model.get_feature_importance()
        logger.info(f"columns: {X_train.columns}")
        feature_importance_df = pd.DataFrame(
            {"feature": X_train.columns, "importance": importances}
        ).sort_values("importance", ascending=False)

        # Save to a file inside your output directory
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        feature_importance_path = output_dir / "feature_importance.json"
        feature_importance_df.to_json(
            feature_importance_path, orient="records", indent=2
        )

        # store the path (not the JSON string)
        self.log_data["artifacts"].append(feature_importance_path)

        return y_train_true, y_train_pred

    def _validate_model(self, validation_set: pd.DataFrame) -> Tuple[YType, YType]:
        """
        Check how well model generalizes during development
        The mock exam:
        If models were student, this is used to check progress, adjust study strategies, and identify weaknesses.
        Used to tune hyperparameters or choose the best model
        """
        # validation - tuning / model selection for evalution performance to know which model is best
        # inference validation set
        y_val_true, y_val_pred = self.predict(validation_set)
        val_rmse = root_mean_squared_error(y_val_true, y_val_pred)
        val_mse = mean_squared_error(y_val_true, y_val_pred)
        # r^2: how much of that variability is captured by model's predictions
        val_r2 = r2_score(y_val_true, y_val_pred)
        self.log_data["metrics"]["val_rmse"] = val_rmse
        self.log_data["metrics"]["val_mse"] = val_mse
        self.log_data["metrics"]["val_r2"] = val_r2

        return y_val_true, y_val_pred

    def _test_model(self, test_set: pd.DataFrame) -> Tuple[YType, YType]:
        """
        Simulate real-world, unseen data performance
        The real exam:
        If models were student, they never seen each problems before and gives the final unbiased measure of knowledge.
        Used only once — after all model tuning is finished
        """

        # inference test set
        y_true, y_pred = self.predict(test_set)
        # rmse: how large your prediction errors are on avg
        rmse = root_mean_squared_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)

        self.log_data["metrics"]["rmse"] = rmse
        # for learning progress
        self.log_data["metrics"]["mse"] = mse

        return y_true, y_pred

    def _evaluate_regression_metrics(
        self, y_true: YType, y_pred: YType, metric_type: MetricType
    ) -> Dict[str, float]:
        rmse = root_mean_squared_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)

        return {
            f"{metric_type.value}_rmse": rmse,
            f"{metric_type.value}_mse": mse,
            f"{metric_type.value}_r2": r2,
        }

    def _log_all_metrics(self, metric_map: Dict[str, float]):
        for metric, value in metric_map.items():
            self.log_data["metrics"][metric] = value

    # ---------- public API ---------------------------------------------
    def train_and_evaluate(self, df: pd.DataFrame, checksum: str):
        self.log_data["text"]["columns_used"] = df.columns

        train, test, val = self._train_test_split(df)

        y_train_true, y_train_pred = self._train_model(train, val)
        y_val_true, y_val_pred = self._validate_model(val)
        y_true, y_pred = self._test_model(test)

        train_metrics = self._evaluate_regression_metrics(
            y_train_true, y_train_pred, MetricType.TRAIN
        )
        validation_metrics = self._evaluate_regression_metrics(
            y_val_true, y_val_pred, MetricType.VALIDATION
        )
        test_metrics = self._evaluate_regression_metrics(
            y_true, y_pred, MetricType.TEST
        )

        self._log_all_metrics({**train_metrics, **validation_metrics, **test_metrics})

        self.log_data["params"]["raw_csv_sha256"] = checksum

    def predict(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        X = df.drop(columns="price")
        y_true = np.asarray(df["price"].values)
        y_pred = self.model.predict(X)
        if self.cfg.log_target:
            y_pred = np.expm1(y_pred)
        y_pred = np.asarray(y_pred)
        return y_true, y_pred
