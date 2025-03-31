# Open Dental Embeddings

This directory contains the specialized embeddings for Open Dental documentation.

## Directory Structure

- `/chunks` - Individual embedding chunks stored as JSON files
- `/stats` - Statistics and metadata about the embedding process
- `embedding_chunks.json` - Combined file with all embedding chunks

## Embedding Types

The embeddings in this directory follow the specialized approach outlined in the project:

1. **Content Embeddings** - Main text chunks from API documentation, database schemas, and user manuals
2. **Metadata Embeddings** - Tags, categories, and version info attached to each chunk
3. **Relationship Embeddings** - Connections between components for graph-like queries

## Usage

These embedding files are used with the `upload_to_vector_db.py` script to populate a vector database, which can then be queried using the `query_vector_db.py` script.

## Stats

The `/stats` directory contains JSON files with statistics about the embedding process, including:

- Total number of chunks
- Breakdown by document type (API, database, manual, relationships)
- Chunk size and overlap settings
- Timestamp of the embedding process

The most recent stats file can be used to evaluate the quality of the embeddings and adjust parameters as needed.
