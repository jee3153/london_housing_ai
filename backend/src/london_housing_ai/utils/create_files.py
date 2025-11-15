from pathlib import Path
from pandas import DataFrame
from typing import Dict, Any
import json

ARTIFACT_DIR = Path("artifacts")


def generate_artifact_from_df(filename: str, df: DataFrame) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    feature_importance_path = ARTIFACT_DIR / filename
    df.to_json(feature_importance_path, orient="records", indent=2)
    return feature_importance_path


def generate_artifact_from_payload(filename: str, payload: Dict[str, Any]) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACT_DIR / filename
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return report_path
