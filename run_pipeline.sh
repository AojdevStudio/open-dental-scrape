#!/bin/bash
#
# Run the Open Dental documentation embedding pipeline
#

# Load environment variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "Error: .env file not found"
  exit 1
fi

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
  echo "Error: OPENAI_API_KEY is not set in .env file"
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

# Step 1: Prepare code embeddings
echo "Step 1: Preparing code embeddings..."
python scripts/prepare_code_embeddings.py \
  --input-dir $INPUT_DIR \
  --output-dir $OUTPUT_DIR \
  --chunk-size 1000 \
  --chunk-overlap 200

# Check if Step 1 succeeded
if [ $? -ne 0 ]; then
  echo "Error: Failed to prepare code embeddings"
  exit 1
fi

# Step 2: Generate local embeddings
echo "Step 2: Generating local embeddings..."
python scripts/prepare_local_embeddings.py \
  --input-dir $OUTPUT_DIR \
  --output-dir $EMBEDDINGS_DIR

# Check if Step 2 succeeded
if [ $? -ne 0 ]; then
  echo "Error: Failed to generate local embeddings"
  exit 1
fi

# Step 3: Print next steps
echo ""
echo "====================================================="
echo "Embeddings generation completed successfully!"
echo "====================================================="
echo ""
echo "Local embeddings have been saved to: $EMBEDDINGS_DIR"
echo ""
echo "Next steps:"
echo "1. Use these embeddings with a vector database of your choice:"
echo "   - Pinecone (https://www.pinecone.io/)"
echo "   - Weaviate (https://weaviate.io/)"
echo "   - Qdrant (https://qdrant.tech/)"
echo "   - ChromaDB (https://www.trychroma.com/)"
echo ""
echo "2. Once you've set up your vector database, you can query it using:"
echo "   - Your database's native query interface"
echo "   - A custom frontend for OpenDental documentation"
echo ""
echo "3. Sample integration code templates can be found in README.md"
echo "====================================================="
