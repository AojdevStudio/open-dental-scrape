#!/bin/bash
# run_processing.sh - Install dependencies and run the processing scripts

# Find the Python3 command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Neither python3 nor python command found. Please install Python 3."
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"

# Create a virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv env

# Activate virtual environment
echo "Activating virtual environment..."
source env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install beautifulsoup4 requests argparse pathlib

# Run the processing script
echo "Running processing script..."
python process_all_docs_fixed.py --pip-install

# Deactivate virtual environment
deactivate

echo "Processing complete. See the /docs/processed directory for results."
