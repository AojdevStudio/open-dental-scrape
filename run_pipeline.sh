#!/bin/bash
#
# Run the Open Dental documentation embedding pipeline
#

# Load environment variables from .env file
if [ -f .env ]; then
  source .env
else
  echo "Error: .env file not found"
  exit 1
fi

# Check required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
  echo "Error: OPENAI_API_KEY is not set. Please add it to your .env file."
  exit 1
fi

# Set directories
INPUT_DIR="/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed"
OUTPUT_DIR="/Users/aojdevstudio/cursor-projects/open-dental-scrape/embeddings"
EMBEDDINGS_DIR="/Users/aojdevstudio/cursor-projects/open-dental-scrape/local_embeddings"

# Create output directories
mkdir -p $OUTPUT_DIR/chunks
mkdir -p $OUTPUT_DIR/stats
mkdir -p $EMBEDDINGS_DIR

# Parse command line options
FORCE_REFRESH=false

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --force-refresh)
      FORCE_REFRESH=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./run_pipeline.sh [--force-refresh]"
      echo "  --force-refresh    Force refresh all embeddings even if they exist"
      exit 1
      ;;
  esac
done

echo "====================== Open Dental Documentation Embedding Pipeline ======================"
echo "This script will process the Open Dental documentation and create embeddings for use"
echo "with various vector databases."
echo ""
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Local embeddings directory: $EMBEDDINGS_DIR"
echo "Force refresh: $FORCE_REFRESH"
echo ""

# Step 1: Prepare code embeddings
echo "[1/2] Preparing code embeddings..."
python scripts/prepare_code_embeddings.py --input-dir "$INPUT_DIR" --output-dir "$OUTPUT_DIR" --chunk-size 1000 --chunk-overlap 200

# Check if the previous step succeeded
if [ $? -ne 0 ]; then
  echo "Error: Failed to prepare embeddings"
  exit 1
fi

# Step 2: Generate local embeddings
echo "[2/2] Generating local embeddings..."

# Add force-refresh flag if needed
FORCE_FLAG=""
if [ "$FORCE_REFRESH" = true ]; then
  FORCE_FLAG="--force-refresh"
fi

python scripts/prepare_local_embeddings.py --input-dir "$OUTPUT_DIR" --output-dir "$EMBEDDINGS_DIR" $FORCE_FLAG

# Check if the previous step succeeded
if [ $? -ne 0 ]; then
  echo "Error: Failed to generate local embeddings"
  exit 1
fi

echo ""
echo "====================== Pipeline Completed Successfully! ======================"
echo ""
echo "Your embeddings are now ready for use with various vector databases."
echo ""
echo "Next steps:"
echo "1. Import the embeddings into Chroma, Pinecone, or another vector database."
echo "2. Use the embeddings with your retrieval system."
echo ""
echo "For more information, please refer to the documentation."
echo ""
