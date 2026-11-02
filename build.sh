#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Run data pipeline and initialize/seed database
python scripts/data_pipeline.py
python scripts/seed_database.py
