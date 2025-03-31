#!/bin/bash
#
# Run the entire Open Dental documentation embedding pipeline
#

# Set these variables
# Replace with your actual OpenAI API key before running
OPENAI_API_KEY="your_openai_api_key_here"
INPUT_DIR="/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed"
OUTPUT_DIR="/Users/aojdevstudio/cursor-projects/open-dental-scrape/embeddings"
INDEX_NAME="open_dental_docs"
INDEX_DESC="Open Dental documentation for code understanding"

# Create output directories
mkdir -p $OUTPUT_DIR/chunks
mkdir -p $OUTPUT_DIR/stats

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

# Step 2: Upload to vector database
echo "Step 2: Uploading to vector database..."
python scripts/upload_to_vector_db.py \
  --input-dir $OUTPUT_DIR \
  --openai-api-key $OPENAI_API_KEY \
  --index-name $INDEX_NAME \
  --index-description "$INDEX_DESC"

# Check if Step 2 succeeded
if [ $? -ne 0 ]; then
  echo "Error: Failed to upload to vector database"
  exit 1
fi

# Get the index ID from the stats file
INDEX_ID=$(jq -r '.index_id' $OUTPUT_DIR/stats/upload_stats_*.json | tail -n 1)

if [ -z "$INDEX_ID" ]; then
  echo "Error: Could not find index ID in stats files"
  exit 1
fi

# Step 3: Test query
echo "Step 3: Testing query..."
echo "Running test query: How do I create a new patient using the API?"
python scripts/query_vector_db.py \
  --openai-api-key $OPENAI_API_KEY \
  --index-id $INDEX_ID \
  --query "How do I create a new patient using the API?"

echo ""
echo "====================================================="
echo "Pipeline completed successfully!"
echo "====================================================="
echo "Vector Index ID: $INDEX_ID"
echo ""
echo "You can now query the vector database using:"
echo "python scripts/query_vector_db.py --openai-api-key \$OPENAI_API_KEY --index-id $INDEX_ID --query \"Your query here\""
echo ""
echo "Example queries:"
echo "- How do I update a patient's insurance information?"
echo "- What tables are related to appointments?"
echo "- Explain the billing workflow in Open Dental"
echo "====================================================="
