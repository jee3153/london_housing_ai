import csv
from london_housing_ai.loaders import (
    load_dataset,
    load_cleaning_config,
    load_augment_config,
    load_train_config,
)
from pathlib import Path
from pandas import DataFrame
from pandas.testing import assert_frame_equal
import os
from typing import List, Any
import pytest


def test_load_noheader_dataset():
    headers = ["StudentID", "FirstName", "LastName", "Age", "Grade"]
    data_to_save = [
        [1, "Alice", "Smith", 16, 10],
        [2, "Bob", "Johnson", 17, 11],
        [3, "Charlie", "Brown", 16, 10],
    ]

    current_dir = Path(__file__).resolve().parent
    file_path = current_dir / "students_simple.noheader.csv"

    _save_csv_file(file_path, data_to_save)

    loaded_df = load_dataset(
        file_path, headers, ["FirstName", "LastName", "Age", "Grade"]
    )
    expected = DataFrame(
        {
            "FirstName": ["Alice", "Bob", "Charlie"],
            "LastName": ["Smith", "Johnson", "Brown"],
            "Age": [16, 17, 16],
            "Grade": [10, 11, 10],
        }
    )
    assert_frame_equal(loaded_df, expected)
    os.remove(file_path)


def test_load_headered_dataset():
    headers = ["StudentID", "FirstName", "LastName", "Age", "Grade"]
    data_to_save = [
        [1, "Alice", "Smith", 16, 10],
        [2, "Bob", "Johnson", 17, 11],
        [3, "Charlie", "Brown", 16, 10],
    ]

    current_dir = Path(__file__).resolve().parent
    file_name = current_dir / "students_simple.csv"

    _save_csv_file(file_name, data_to_save)

    loaded_df = load_dataset(
        file_name, headers, ["FirstName", "LastName", "Age", "Grade"]
    )
    expected = DataFrame(
        {
            "FirstName": ["Bob", "Charlie"],
            "LastName": ["Johnson", "Brown"],
            "Age": [17, 16],
            "Grade": [11, 10],
        }
    )
    assert_frame_equal(loaded_df, expected)
    os.remove(file_name)


def test_load_cleaning_config():
    path = Path(__file__).parent
    config = load_cleaning_config(path / "test_resources/test_cleaning_config.yaml")

    assert config.clip_price == True
    assert config.postcode_col == "postcodes"
    assert config.dtype_map == {"col1": "float", "col2": "datetime"}
    assert config.clip_price == True
    assert config.clip_quantile == 0.5
    assert config.col_headers == ["price", "date"]


def test_load_invalid_cleaning_config():
    path = _get_dir_path() / "test_resources/invalid_test_config.yaml"
    with pytest.raises(
        KeyError, match=r"cleaning config is not configured properly. reason - .*"
    ):
        load_cleaning_config(path)


def test_load_missing_field_cleaning_config():
    path = _get_dir_path() / "test_resources/missing_keys_cleaning_config.yaml"
    with pytest.raises(KeyError, match=r"cleaning configuration field missing. .*"):
        load_cleaning_config(path)


def test_load_invalid_augment_config():
    path = _get_dir_path()
    config = load_augment_config(path / "test_resources/invalid_test_config.yaml")
    assert config == None


def test_load_missing_field_augment_config():
    path = _get_dir_path()
    with pytest.raises(KeyError, match=r"configuration field missing. .*"):
        load_augment_config(path / "test_resources/missing_keys_aug_config.yaml")


def test_load_train_config():
    path = _get_dir_path() / "test_resources/test_train_config.yaml"
    config = load_train_config(path)
    assert config != None
    assert config.cat_features == ["property_type", "old/new", "district"]
    assert config.log_target == True
    assert config.clip_target_q == 0.99
    assert config.test_size == 0.15
    assert config.val_size == 0.15
    assert config.random_state == 42
    assert config.n_iter == 4000
    assert config.depth == 8
    assert config.lr == 0.05
    assert config.early_stop == 200


def _save_csv_file(file_path: Path, data_to_save: List[List[Any]]):
    """
    write data as csv as a file name in current dir
    """
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        # create csv write object
        writer = csv.writer(file)
        # write all rows at once
        writer.writerows(data_to_save)


def _get_dir_path() -> Path:
    """
    get current directory path
    """
    return Path(__file__).resolve().parent
