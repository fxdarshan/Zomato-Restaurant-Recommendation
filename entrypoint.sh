#!/usr/bin/env bash
set -e

echo "======================================================="
echo "Starting Zomato AI Restaurant Recommendation Service..."
echo "======================================================="

# Ensure data directories exist
mkdir -p data/raw data/processed

# Check if cleaned dataset is present
PARQUET_FILE="data/processed/zomato_cleaned.parquet"

if [ ! -f "$PARQUET_FILE" ]; then
    echo "[INFO] Cleaned dataset not found at $PARQUET_FILE."
    echo "[INFO] Running automated ETL pipeline from Hugging Face..."
    python -m src.data_pipeline.download_dataset
    python -m src.data_pipeline.preprocess
    echo "[INFO] ETL pipeline completed successfully."
else
    echo "[INFO] Verified pre-processed dataset at $PARQUET_FILE."
fi

# Determine port (supports Cloud Run, Render, Railway dynamic $PORT or default 8000)
SERVER_PORT="${PORT:-8000}"
SERVER_HOST="${HOST:-0.0.0.0}"

echo "[INFO] Launching Uvicorn server on $SERVER_HOST:$SERVER_PORT..."
exec uvicorn src.api.main:app --host "$SERVER_HOST" --port "$SERVER_PORT"
