# Open Dental Documentation Embeddings

This project creates specialized embeddings for Open Dental API, database schema, and manual documentation. These embeddings are designed to capture code relationships and context, enabling more accurate semantic search and retrieval.

## Overview

The project consists of three main scripts:

1. `prepare_code_embeddings.py` - Processes the scraped Open Dental documentation and prepares it for embedding.
2. `upload_to_vector_db.py` - Uploads the processed embeddings to an OpenAI vector database.
3. `query_vector_db.py` - Provides a CLI interface to query the vector database.

## Prerequisites

- Python 3.8+
- OpenAI API key
- Open Dental documentation in the processed format

## Installation

1. Clone this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your OpenAI API key:
```bash
# Example .env file
OPENAI_API_KEY=your_openai_api_key_here
VECTOR_INDEX_NAME=open_dental_docs
VECTOR_INDEX_DESCRIPTION="Open Dental documentation for code understanding"
```

> **Important:** Add the `.env` file to your `.gitignore` to avoid exposing your API key in version control.

## Usage

### Running the Complete Pipeline

The easiest way to run the complete pipeline is to use the provided script:

```bash
# Make sure the script is executable
chmod +x run_pipeline.sh

# Run the pipeline
./run_pipeline.sh
```

This will:
1. Load your API key from the `.env` file
2. Process the documentation to create embeddings
3. Generate vector embeddings and save them locally
4. Provide next steps for using the embeddings with vector databases

### Using Generated Embeddings

The pipeline creates three types of specialized embeddings:
- Content Embeddings: Main text content from API, database, and manual documentation
- Metadata Embeddings: Tags, categories, and version information
- Relationship Embeddings: Connections between components (APIs, database tables, etc.)

#### Integration with Vector Databases

You can use the generated embeddings with various vector databases:

##### Pinecone

```python
import pinecone
from pathlib import Path
import json

# Initialize Pinecone
pinecone.init(api_key="YOUR_API_KEY", environment="YOUR_ENVIRONMENT")

# Create index if it doesn't exist
if "open_dental" not in pinecone.list_indexes():
    pinecone.create_index("open_dental", dimension=1536)  # Ada-002 uses 1536 dimensions

# Connect to the index
index = pinecone.Index("open_dental")

# Load embeddings
embeddings_dir = Path("/path/to/local_embeddings")
combined_file = embeddings_dir / "combined_embeddings.json"

with open(combined_file, "r") as f:
    data = json.load(f)
    chunks = data["chunks"]

# Prepare vectors for upsert
vectors = []
for chunk in chunks:
    vectors.append({
        "id": chunk["id"],
        "values": chunk["embedding"],
        "metadata": {
            "text": chunk["text"],
            "type": chunk["metadata"]["type"],
            "title": chunk["metadata"]["title"]
        }
    })

# Upsert in batches
batch_size = 100
for i in range(0, len(vectors), batch_size):
    batch = vectors[i:i + batch_size]
    index.upsert(vectors=batch)
```

##### Weaviate

```python
import weaviate
import json
from pathlib import Path

# Connect to Weaviate
client = weaviate.Client("http://localhost:8080")

# Create schema
class_obj = {
    "class": "OpenDental",
    "properties": [
        {"name": "text", "dataType": ["text"]},
        {"name": "title", "dataType": ["string"]},
        {"name": "type", "dataType": ["string"]},
        {"name": "category", "dataType": ["string"]}
    ]
}

# Add the schema
client.schema.create_class(class_obj)

# Load embeddings
embeddings_dir = Path("/path/to/local_embeddings")
combined_file = embeddings_dir / "combined_embeddings.json"

with open(combined_file, "r") as f:
    data = json.load(f)
    chunks = data["chunks"]

# Import data
for chunk in chunks:
    # Import with vector
    client.data_object.create(
        data_object={
            "text": chunk["text"],
            "title": chunk["metadata"]["title"],
            "type": chunk["metadata"]["type"],
            "category": chunk["metadata"].get("category", "")
        },
        class_name="OpenDental",
        vector=chunk["embedding"]
    )
```

##### Qdrant

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import json
from pathlib import Path

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="open_dental",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

# Load embeddings
embeddings_dir = Path("/path/to/local_embeddings")
combined_file = embeddings_dir / "combined_embeddings.json"

with open(combined_file, "r") as f:
    data = json.load(f)
    chunks = data["chunks"]

# Prepare points for upload
points = []
for chunk in chunks:
    points.append({
        "id": chunk["id"],
        "vector": chunk["embedding"],
        "payload": {
            "text": chunk["text"],
            "title": chunk["metadata"]["title"],
            "type": chunk["metadata"]["type"],
            "category": chunk["metadata"].get("category", "")
        }
    })

# Upload in batches
batch_size = 100
for i in range(0, len(points), batch_size):
    batch = points[i:i + batch_size]
    client.upsert(
        collection_name="open_dental",
        points=batch
    )
```

### Running Individual Components

If you prefer to run components separately:

#### 1. Prepare Code Embeddings

Process the Open Dental documentation to create specialized embeddings:

```bash
python scripts/prepare_code_embeddings.py \
  --input-dir /path/to/processed/docs \
  --output-dir /path/to/output
```

This will:
- Load documentation from the input directory
- Extract relationships between different components
- Create context-aware chunks suitable for embedding
- Enrich chunks with metadata for better retrieval
- Save the processed chunks to the output directory

#### 2. Upload to Vector Database

Upload the processed embeddings to an OpenAI vector database:

```bash
# If using environment variables
python scripts/upload_to_vector_db.py \
  --input-dir /path/to/processed/embeddings

# Or with explicit parameters
python scripts/upload_to_vector_db.py \
  --input-dir /path/to/processed/embeddings \
  --openai-api-key YOUR_API_KEY \
  --index-name open_dental_docs \
  --index-description "Open Dental documentation for code understanding"
```

This will:
- Load the processed embedding chunks
- Create embedding vectors using the OpenAI API
- Create a new vector index in OpenAI
- Upload the chunks with embedding vectors to the vector index
- Save upload statistics to the stats directory

#### 3. Query Vector Database

Query the vector database to retrieve relevant documentation:

```bash
# If using environment variables and the index ID is stored in stats
python scripts/query_vector_db.py \
  --index-id YOUR_INDEX_ID \
  --query "How to create a patient using the API?"

# Or with explicit parameters
python scripts/query_vector_db.py \
  --openai-api-key YOUR_API_KEY \
  --index-id YOUR_INDEX_ID \
  --query "How to create a patient using the API?"
```

> **Note:** The index ID is returned when you upload the embeddings and is saved in the stats directory.

This will:
- Create an embedding vector for the query
- Search the vector index for matching documents
- Enhance the results with generated context
- Generate a comprehensive answer based on the search results
- Output the answer and search results

#### Additional Options

- `--top-k` - Number of top results to return (default: 5)
- `--no-enhance` - Disable result enhancement
- `--json` - Output results as JSON

## Directory Structure

After running the scripts, the directory structure will look like this:

```
/path/to/output/
├── chunks/               # Individual embedding chunks
├── metadata/             # Metadata about the processing
├── relationships/        # Extracted relationships
│   ├── all_relationships.json
│   └── relationship_graph.json
├── stats/                # Upload statistics
└── embedding_chunks.json # Combined embedding chunks
```

## Features

### Specialized Code Embeddings

The embeddings are specifically designed for code documentation:

- **Relationship-aware**: Captures relationships between API endpoints, database tables, and manual sections
- **Context-preserving**: Maintains context across chunk boundaries
- **Metadata-rich**: Includes metadata for better filtering and retrieval

### Enhanced Search Results

The query tool enhances search results with generated context:

- **Relevance scores**: Rates the relevance of each result to the query
- **Contextual analysis**: Provides additional context to understand each result
- **Comprehensive answers**: Generates a complete answer based on all search results

## Use Cases

- **API Integration**: Find relevant API endpoints and understand their usage
- **Database Schema Understanding**: Explore database tables and their relationships
- **Code Relationships**: Discover how different components interact with each other
- **Documentation Exploration**: Navigate through the Open Dental documentation

## Note

This project is designed for educational and research purposes. Please ensure you have the appropriate rights to use the Open Dental documentation before using these scripts.
