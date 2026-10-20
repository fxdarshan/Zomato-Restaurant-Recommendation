"""Dataset ingestion module for the Zomato restaurant dataset from Hugging Face."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
from typing import Optional

# Ensure project root is in sys.path for direct CLI script execution
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from datasets import load_dataset
import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)


def download_dataset(
    dataset_id: str = settings.HUGGINGFACE_DATASET_ID,
    output_path: Path | str = settings.RAW_DATA_PATH,
    split: str = "train",
    force: bool = False,
) -> Path:
    """Fetch raw Zomato dataset from Hugging Face and persist to raw CSV.

    Args:
        dataset_id: Hugging Face dataset identifier.
        output_path: Destination path for the raw CSV.
        split: Dataset split to download.
        force: If True, re-download even if the raw file already exists.

    Returns:
        Path to the saved raw CSV file.
    """
    dest_path = Path(output_path).resolve()

    if dest_path.exists() and not force:
        file_size_mb = dest_path.stat().st_size / (1024 * 1024)
        logger.info(
            "Raw dataset already exists at %s (%.2f MB). Skipping download.",
            dest_path,
            file_size_mb,
        )
        return dest_path

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading dataset '%s' (split='%s') from Hugging Face...", dataset_id, split)

    try:
        hf_ds = load_dataset(dataset_id, split=split)
    except Exception as exc:
        logger.error("Failed to download dataset from Hugging Face: %s", exc)
        raise RuntimeError(f"Error fetching dataset '{dataset_id}': {exc}") from exc

    df: pd.DataFrame = hf_ds.to_pandas()
    logger.info("Loaded %d rows from Hugging Face. Saving to %s...", len(df), dest_path)

    df.to_csv(dest_path, index=False, encoding="utf-8")
    file_size_mb = dest_path.stat().st_size / (1024 * 1024)
    logger.info("Successfully saved raw dataset to %s (%.2f MB, %d rows).", dest_path, file_size_mb, len(df))

    return dest_path


def main() -> None:
    """CLI entrypoint for dataset download."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Download Zomato dataset from Hugging Face Hub")
    parser.add_argument(
        "--dataset-id",
        type=str,
        default=settings.HUGGINGFACE_DATASET_ID,
        help="Hugging Face dataset identifier",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(settings.RAW_DATA_PATH),
        help="Destination path for raw CSV",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if file exists",
    )

    args = parser.parse_args()
    download_dataset(dataset_id=args.dataset_id, output_path=args.output, force=args.force)


if __name__ == "__main__":
    main()
