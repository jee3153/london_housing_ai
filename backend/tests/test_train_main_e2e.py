import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.gcs
def test_train_main_e2e(request: pytest.FixtureRequest):
    root = Path(request.config.rootpath)
    config_file = (
        root / "src" / "london_housing_ai" / "configs" / "config_dataset2.yaml"
    )
    csv_file = root / "tests" / "fixtures" / "sample_housing.csv"

    env = os.environ
    env["PYTHONPATH"] = str(Path(request.config.rootpath) / "src")

    result = subprocess.run(
        [
            "python",
            "-m",
            "london_housing_ai.train_main",
            "--config",
            config_file,
            "--csv",
            csv_file,
        ],
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )

    assert result.returncode == 0, f"Train pipeline failed:\n{result.stderr}"
    assert "the experiment of model has completed." in result.stdout
