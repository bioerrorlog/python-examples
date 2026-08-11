"""Mirror test data and results between the local run and Cloud Storage."""

import os
import subprocess
from pathlib import Path

DATA_GCS_URI = os.environ.get(
    "DATA_GCS_URI",
    "gs://your-gcs-bucket-name/exe_api_calls/data",
)
RESULTS_GCS_URI = os.environ.get(
    "RESULTS_GCS_URI",
    "gs://your-gcs-bucket-name/exe_api_calls/results",
)


def sync_data_from_gcs(local_data_dir: Path) -> None:
    """Mirror local_data_dir from the canonical test data kept in Cloud Storage.

    This is a one-way mirror: local files not present in Cloud Storage are
    deleted, so local_data_dir should not be edited by hand.
    """
    subprocess.run(
        ["gsutil", "-m", "rsync", "-r", "-d", DATA_GCS_URI, str(local_data_dir)],
        check=True,
    )


def upload_results_to_gcs(local_results_run_dir: Path) -> None:
    """Upload one run's results directory to Cloud Storage."""
    subprocess.run(
        ["gsutil", "-m", "cp", "-r", str(local_results_run_dir), f"{RESULTS_GCS_URI}/"],
        check=True,
    )
