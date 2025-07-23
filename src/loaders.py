from typing import List, Dict, Any
import pandas as pd
from pandas import DataFrame
import yaml
from src.config_schemas.CleaningConfig import CleaningConfig
from src.config_schemas.AugmentConfig import AugmentConfig
from src.config_schemas.TrainConfig import TrainConfig
from src.config_schemas.ParquetConfig import ParquetConfig
from src.config_schemas.FeatureConfig import FeatureConfig, CityFilter
from pathlib import Path


def load_dataset(
    path: Path, schema: List[str], columns_to_load: List[str]
) -> DataFrame:
    is_noheader = path.suffixes == [".noheader", ".csv"]
    try:
        return pd.read_csv(
            path,
            header=None if is_noheader else 0,
            names=schema,
            usecols=columns_to_load,
        )
    except:
        raise RuntimeError("schema and column header doesn't match.")


def load_cleaning_config(path: Path) -> CleaningConfig:
    try:
        raw_config = _load_config(path)["cleaning"]
    except Exception as e:
        raise KeyError(f"cleaning config is not configured properly. reason - {e}")

    size_dtype_map = len(raw_config["dtype_map"].items())
    size_required_cols = len(raw_config["required_cols"])

    if size_dtype_map != size_required_cols:
        raise RuntimeError(
            "size of dtype_map (={size_dtype_map}) should be the same as size of required_cols (={size_required_cols}) in config."
        )

    config_args = {k: v for k, v in raw_config.items() if v is not None}

    try:
        return CleaningConfig(**config_args)
    except Exception as e:
        raise KeyError(f"cleaning configuration field missing. {e}")


def load_augment_config(path: Path) -> AugmentConfig | None:
    raw_config = _load_config(path)
    try:
        raw_config = raw_config["augment_dataset"]
    except:
        return None

    config_args = {k: v for k, v in raw_config.items() if v is not None}

    try:
        return AugmentConfig(**config_args)
    except Exception as e:
        raise KeyError(f"aug configuration field missing. {e}")


def load_train_config(path: Path) -> TrainConfig:
    try:
        raw_config = _load_config(path)["train"]
    except Exception as e:
        raise KeyError(f"train config is not configured properly. reason - {e}")

    # Remove keys with None values so dataclass uses its defaults
    config_args = {k: v for k, v in raw_config.items() if v is not None}
    try:
        return TrainConfig(**config_args)
    except Exception as e:
        raise KeyError(f"train configuration field missing. {e}")


def load_fe_config(path: Path) -> FeatureConfig:
    raw_config = _load_config(path)
    try:
        raw_config = raw_config["feature_engineering"]
    except Exception as e:
        raise KeyError(f"feature config is not configured properly. reason - {e}")

    if raw_config.get("city_filter"):
        raw_config["city_filter"] = CityFilter(**raw_config["city_filter"])
    config_args = {k: v for k, v in raw_config.items() if v is not None}

    try:
        return FeatureConfig(**config_args)
    except Exception as e:
        raise KeyError(f"feature configuration field missing. {e}")


def load_parquet_config(path: Path) -> ParquetConfig:
    raw_config = _load_config(path)
    try:
        raw_config = raw_config["parquet"]
    except Exception as e:
        raise KeyError(f"parquet config is not configured properly. reason - {e}")

    config_args = {k: v for k, v in raw_config.items() if v is not None}

    try:
        return ParquetConfig(**config_args)
    except Exception as e:
        raise KeyError(f"parquet configuration field missing. {e}")


def _load_config(path: Path) -> Dict[Any, Any]:
    with open(path) as f:
        return yaml.safe_load(f)
