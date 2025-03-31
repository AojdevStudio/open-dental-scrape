# OpenDental Documentation Processing Scripts

This directory contains scripts to process and structure OpenDental documentation for use with vector stores and AI systems.

## Overview

These scripts transform the raw OpenDental documentation into structured JSON files that are optimized for:
- Vector embeddings
- Relationship mapping
- AI context retrieval
- MCP (Model Context Protocol) server integration

## Prerequisites

- Python 3.8 or higher
- Required Python packages:
  ```
  pip install argparse pathlib
  ```

## Directory Structure

The scripts expect the following directory structure:

```
open-dental-scrape/
├── docs/
│   ├── api-documentation/        # API documentation text files
│   ├── database-documentation/   # Database schema documentation
│   ├── manual-documentation/     # Manual content in JSON format
│   └── processed/                # Output directory (created by scripts)
└── scripts/                      # The processing scripts
```

## Scripts

### 1. process_all_docs.py

Main script that runs all the processing steps in sequence.

```bash
python process_all_docs.py [--output PATH] [--scripts PATH]
```

Arguments:
- `--output`: Output directory for processed documentation (default: `/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed`)
- `--scripts`: Directory containing processing scripts (default: `/Users/aojdevstudio/cursor-projects/open-dental-scrape/scripts`)

### 2. process_api_docs.py

Processes API documentation text files into structured JSON.

```bash
python process_api_docs.py [--input PATH] [--output PATH]
```

Arguments:
- `--input`: Input directory containing API text files (default: `/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/api-documentation`)
- `--output`: Output directory for structured JSON files (default: `/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed/api`)

### 3. process_db_docs.py

Processes database documentation into structured JSON, with one file per table.

```bash
python process_db_docs.py [--input PATH] [--output PATH]
```

Arguments:
- `--input`: Input database documentation file (default: `/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/database-documentation/open_dental_db_docs.md`)
- `--output`: Output directory for structured JSON files (default: `/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed/database`)

### 4. process_manual_docs.py

Processes manual documentation from JSON into structured hierarchical format.

```bash
python process_manual_docs.py [--input PATH] [--output PATH]
```

Arguments:
- `--input`: Input manual documentation JSON file (default: `/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/manual-documentation/manual_content.json`)
- `--output`: Output directory for structured JSON files (default: `/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed/manual`)

### 5. generate_relationships.py

Generates cross-references and relationships between all documentation types.

```bash
python generate_relationships.py [--dir PATH]
```

Arguments:
- `--dir`: Base directory containing processed documentation (default: `/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed`)

## Output Structure

The scripts generate the following structure:

```
docs/processed/
├── api/                # API documentation JSON files
│   ├── api-recalls.json
│   ├── api-patients.json
│   └── ...
├── database/           # Database table documentation JSON files
│   ├── db-patient.json
│   ├── db-appointment.json
│   └── ...
├── manual/             # Manual documentation JSON files
│   ├── manual-recall-setup.json
│   ├── manual-patient-information.json
│   └── ...
├── combined/           # Combined documentation
│   └── index.json      # Master index of all documentation
├── relationship_graph.json  # JSON representation of all relationships
└── manifest.json       # Processing information and statistics
```

Each JSON file follows a standardized schema with these common properties:
- `id`: Unique identifier for the document
- `type`: Document type (api, database, or manual)
- `title`: Human-readable title
- `metadata`: Tags, categories, and other metadata
- `relationships`: Cross-references to related documents

## Using with Vector Store

After processing, the structured JSON files can be used with vector stores:

1. **Extract Text and Metadata**: Parse the JSON files and extract the relevant text content and metadata
2. **Generate Embeddings**: Create embeddings for each document using your preferred embedding model
3. **Store in Vector Database**: Upload the embeddings and metadata to your vector store
4. **Create Relationship Graph**: Use the relationship_graph.json to enhance search with semantic connections

## Sample Vector Store Integration

```python
import json
import os
from pathlib import Path
import openai

# Load processed documents
processed_dir = "/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed"

documents = []
for doc_type in ["api", "database", "manual"]:
    doc_dir = os.path.join(processed_dir, doc_type)
    for file_path in Path(doc_dir).glob("*.json"):
        with open(file_path, 'r') as f:
            doc = json.load(f)
            
            # Extract text content
            if doc_type == "api":
                content = doc.get("content", "")
            elif doc_type == "database":
                content = json.dumps(doc.get("database", {}))
            else:  # manual
                content = json.dumps(doc.get("manual", {}).get("content", []))
            
            # Add to documents
            documents.append({
                "id": doc.get("id"),
                "content": content,
                "metadata": doc.get("metadata", {}),
                "relationships": doc.get("relationships", [])
            })

# Create embeddings and store in vector database
# (Implementation depends on your chosen vector store)
```

## Troubleshooting

If the scripts encounter issues:

1. **File Not Found**: Check the paths in the script arguments
2. **Parsing Errors**: The raw documentation format may have changed; adjust the parsing logic
3. **Memory Issues**: For large documentation files, you might need to increase available memory

## Next Steps After Processing

1. Review the processed files to ensure quality
2. Generate embeddings for each document
3. Store documents and embeddings in your vector store
4. Set up retrieval mechanisms for AI assistants
5. Implement an MCP server to expose this documentation through the Model Context Protocol
