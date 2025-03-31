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
pip install openai tqdm
```

## Usage

### 1. Prepare Code Embeddings

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

### 2. Upload to Vector Database

Upload the processed embeddings to an OpenAI vector database:

```bash
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

### 3. Query Vector Database

Query the vector database to retrieve relevant documentation:

```bash
python scripts/query_vector_db.py \
  --openai-api-key YOUR_API_KEY \
  --index-id YOUR_INDEX_ID \
  --query "How to create a patient using the API?"
```

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
