# Open Dental Documentation Search

This project enables semantic search over Open Dental documentation using vector embeddings.

## Prerequisites

- Python 3.10+
- OpenAI API key
- Qdrant running locally (or remote Qdrant instance)

## Setup

1. Install the required packages:

```bash
pip install qdrant-client openai python-dotenv tqdm
```

2. Create a `.env` file with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

3. Make sure Qdrant is running. To run Qdrant locally using Docker:

```bash
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

## Loading the embeddings

Use the fixed loading script to load your embeddings into Qdrant:

```bash
python load_embeddings_to_qdrant_fixed.py
```

This script:
- Creates a collection named "open_dental_docs" if it doesn't exist
- Loads embeddings from `./local_embeddings/combined_embeddings.json`
- Generates UUID for each document (avoiding the string ID issue)
- Creates a mapping between original IDs and generated UUIDs
- Uploads the embeddings to Qdrant in batches

## Querying the embeddings

Once your embeddings are loaded, you can query them:

```bash
python query_qdrant.py "How to create a patient in Open Dental?"
```

Additional options:
- `--limit` - Number of results to return (default: 5)
- `--filter` - Filter by document type (choices: api, database, manual, relationship)

Example with filtering:
```bash
python query_qdrant.py "How to create a patient in Open Dental?" --filter manual --limit 10
```

## Troubleshooting

If you encounter any issues:

1. Make sure Qdrant is running and accessible
2. Check that your OpenAI API key is valid
3. Verify that your embeddings file exists and is formatted correctly

## Structure of embeddings file

The expected format for `combined_embeddings.json` is:

```json
{
  "chunks": [
    {
      "id": "some-id",
      "text": "Document text content",
      "embedding": [0.1, 0.2, ...],
      "metadata": {
        "title": "Document title",
        "type": "Document type",
        "category": "Optional category"
      }
    },
    ...
  ]
}
```
