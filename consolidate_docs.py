#!/usr/bin/env python3
"""
Script to consolidate embedded chunks into clean documentation files
organized by document type for easier OpenAI vector store indexing.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import re

# Input/output paths
CHUNKS_DIR = Path("./embeddings/chunks")
OUTPUT_DIR = Path("./consolidated_docs")
COMBINED_FILE = Path("./local_embeddings/combined_embeddings.json")

# Create output directory
OUTPUT_DIR.mkdir(exist_ok=True)

def clean_text(text):
    """Clean text to make it more readable"""
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def format_value(value):
    """Safely format a value for output"""
    if isinstance(value, list):
        # Handle lists with dictionary items or other complex types
        items = []
        for item in value:
            if isinstance(item, dict):
                items.append(str(item))
            elif isinstance(item, (list, tuple)):
                items.append(str(item))
            else:
                items.append(str(item))
        return ", ".join(items)
    else:
        return str(value)

def load_combined_file():
    """Load the combined embeddings file if it exists"""
    if COMBINED_FILE.exists():
        print(f"Loading combined embeddings from {COMBINED_FILE}...")
        with open(COMBINED_FILE, 'r') as f:
            return json.load(f)
    return None

def load_chunks():
    """Load all individual chunk files"""
    if not CHUNKS_DIR.exists():
        print(f"Chunks directory {CHUNKS_DIR} not found!")
        return None
    
    print(f"Loading individual chunks from {CHUNKS_DIR}...")
    chunks = []
    for chunk_file in CHUNKS_DIR.glob("*.json"):
        with open(chunk_file, 'r') as f:
            chunk = json.load(f)
            chunks.append(chunk)
    
    return {"chunks": chunks}

def categorize_chunks(data):
    """Group chunks by document type and category"""
    if not data or "chunks" not in data:
        print("No valid chunk data found!")
        return {}
    
    # Group chunks by type and category
    categorized = defaultdict(lambda: defaultdict(list))
    
    for chunk in data["chunks"]:
        if "metadata" not in chunk:
            print(f"Skipping chunk without metadata: {chunk.get('id', 'unknown')}")
            continue
            
        doc_type = chunk["metadata"].get("type", "unknown")
        
        # Determine category based on metadata
        if "section" in chunk["metadata"] and "chapter" in chunk["metadata"]:
            category = f"{chunk['metadata']['section']}-{chunk['metadata']['chapter']}"
        elif "entity_id" in chunk["metadata"]:
            category = chunk["metadata"]["entity_id"].split("-")[0] if "-" in chunk["metadata"]["entity_id"] else "main"
        elif "section" in chunk["metadata"]:
            category = chunk["metadata"]["section"]
        elif "category" in chunk["metadata"]:
            category = chunk["metadata"]["category"]
        else:
            category = "general"
        
        # Ensure category is safe for filenames
        category = re.sub(r'[^\w\-]', '_', category)
        
        # Add to categorized dictionary
        if "text" in chunk:
            categorized[doc_type][category].append(chunk)
        else:
            print(f"Skipping chunk without text: {chunk.get('id', 'unknown')}")
    
    return categorized

def create_consolidated_files(categorized):
    """Create consolidated files from categorized chunks"""
    print(f"Creating consolidated documentation files in {OUTPUT_DIR}...")
    
    # Track document counts
    doc_counts = defaultdict(int)
    
    # Process each document type
    for doc_type, categories in categorized.items():
        # Create directory for the document type
        type_dir = OUTPUT_DIR / doc_type
        type_dir.mkdir(exist_ok=True)
        
        # Process each category within the type
        for category, chunks in categories.items():
            # Sort chunks by any available ordering fields
            try:
                sorted_chunks = sorted(chunks, 
                    key=lambda x: (
                        x["metadata"].get("order", 999),
                        x["metadata"].get("title", "")
                    )
                )
            except Exception as e:
                print(f"Error sorting chunks for {doc_type}/{category}: {e}")
                sorted_chunks = chunks
            
            # Generate content for the file
            content = f"# {doc_type.upper()}: {category}\n\n"
            
            # Add table of contents
            content += "## Contents\n\n"
            for i, chunk in enumerate(sorted_chunks):
                title = chunk["metadata"].get("title", f"Section {i+1}")
                content += f"- {title}\n"
            content += "\n"
            
            # Add each chunk's content
            for i, chunk in enumerate(sorted_chunks):
                title = chunk["metadata"].get("title", f"Section {i+1}")
                content += f"## {title}\n\n"
                content += clean_text(chunk["text"]) + "\n\n"
                
                # Add metadata as comments
                content += "### Metadata\n\n"
                for key, value in chunk["metadata"].items():
                    if key not in ["title"]:  # Skip title as it's already used
                        try:
                            formatted_value = format_value(value)
                            content += f"- {key}: {formatted_value}\n"
                        except Exception as e:
                            print(f"Error formatting metadata {key} for {chunk.get('id', 'unknown')}: {e}")
                content += "\n"
            
            # Write to file
            file_path = type_dir / f"{category}.md"
            with open(file_path, "w") as f:
                f.write(content)
            
            doc_counts[doc_type] += 1
    
    # Print summary
    print("Consolidation complete!")
    print("Document counts by type:")
    for doc_type, count in doc_counts.items():
        print(f"- {doc_type}: {count} files")

if __name__ == "__main__":
    # Try to load the combined file first
    data = load_combined_file()
    
    # If combined file doesn't exist, load individual chunks
    if not data:
        data = load_chunks()
    
    # Categorize chunks
    categorized = categorize_chunks(data)
    
    # Create consolidated files
    if categorized:
        create_consolidated_files(categorized)
    else:
        print("No data to process. Exiting.")
