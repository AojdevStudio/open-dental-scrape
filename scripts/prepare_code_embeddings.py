#!/usr/bin/env python3
"""
Code Embeddings Preparation for Open Dental Documentation
=====================================================

This script processes the API, database, and manual documentation for Open Dental
and prepares it for vector embedding. It creates three types of embeddings:

1. Content Embeddings: Main text chunks optimized for detailed technical queries
2. Metadata Embeddings: Based on tags, categories, and version info for filtering
3. Relationship Embeddings: Connections between components for graph-like queries

Usage:
    python prepare_code_embeddings.py --input-dir /path/to/processed/docs --output-dir /path/to/output

Requirements:
    - tqdm
    - uuid
"""

import argparse
import json
import os
import sys
import uuid
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import re
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmbeddingPreparer:
    """Prepare Open Dental documentation for embedding."""
    
    def __init__(self, input_dir: str, output_dir: str, 
                chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the preparer.
        
        Args:
            input_dir: Directory containing processed documentation
            output_dir: Directory to output embedding-ready chunks
            chunk_size: Maximum size of content chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Create output directories
        self.chunks_dir = self.output_dir / "chunks"
        os.makedirs(self.chunks_dir, exist_ok=True)
        
        # Initialize counters
        self.total_chunks = 0
        self.api_chunks = 0
        self.database_chunks = 0
        self.manual_chunks = 0
        self.relationship_chunks = 0
        
        # Load relationship data if available
        self.relationships = self._load_relationships()
    
    def _load_relationships(self) -> Dict:
        """Load relationship data if available."""
        relationship_file = Path("/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/relationship_graph.json")
        if relationship_file.exists():
            try:
                with open(relationship_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load relationships: {e}")
        
        return {"nodes": [], "edges": []}
    
    def _get_relationship_for_entity(self, entity_id: str) -> List[Dict]:
        """Get relationships for a specific entity."""
        relationships = []
        
        # Find all edges where this entity is source or target
        for edge in self.relationships.get("edges", []):
            if edge.get("source") == entity_id:
                # Find the target node
                target_node = next((node for node in self.relationships.get("nodes", []) 
                                   if node.get("id") == edge.get("target")), None)
                if target_node:
                    relationships.append({
                        "relation_type": edge.get("type", "related_to"),
                        "direction": "outgoing",
                        "target_id": edge.get("target"),
                        "target_name": target_node.get("name", "Unknown"),
                        "target_type": target_node.get("type", "Unknown")
                    })
            
            if edge.get("target") == entity_id:
                # Find the source node
                source_node = next((node for node in self.relationships.get("nodes", []) 
                                   if node.get("id") == edge.get("source")), None)
                if source_node:
                    relationships.append({
                        "relation_type": edge.get("type", "related_to"),
                        "direction": "incoming",
                        "source_id": edge.get("source"),
                        "source_name": source_node.get("name", "Unknown"),
                        "source_type": source_node.get("type", "Unknown")
                    })
        
        return relationships
    
    def _chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """Split text into chunks with optional overlap.
        
        Args:
            text: Text to chunk
            metadata: Metadata to include with each chunk
            
        Returns:
            List of chunk dictionaries
        """
        # Skip if text is empty
        if not text.strip():
            return []
        
        chunks = []
        
        if len(text) <= self.chunk_size:
            # If text is smaller than chunk size, create a single chunk
            chunk_id = str(uuid.uuid4())
            chunks.append({
                "id": chunk_id,
                "text": text,
                "metadata": metadata
            })
        else:
            # Split text into chunks
            start = 0
            chunk_index = 0
            
            while start < len(text):
                # Find a good breakpoint
                end = min(start + self.chunk_size, len(text))
                
                # Try to break at a paragraph or sentence boundary
                if end < len(text):
                    # Look for paragraph break
                    para_break = text.rfind("\n\n", start, end)
                    if para_break > start + self.chunk_size // 2:
                        end = para_break + 2
                    else:
                        # Look for sentence break (period followed by space)
                        sentence_break = text.rfind(". ", start, end)
                        if sentence_break > start + self.chunk_size // 2:
                            end = sentence_break + 2
                
                chunk_id = f"{metadata.get('id', 'doc')}_{chunk_index}"
                chunk_text = text[start:end].strip()
                
                # Copy metadata and add chunk-specific info
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = chunk_index
                chunk_metadata["source_start"] = start
                chunk_metadata["source_end"] = end
                
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": chunk_metadata
                })
                
                # Move to next chunk with overlap
                start = end - self.chunk_overlap if end < len(text) else len(text)
                chunk_index += 1
        
        return chunks
    
    def _add_relationship_context(self, chunks: List[Dict]) -> List[Dict]:
        """Add relationship context to chunks based on relationships graph.
        
        Args:
            chunks: List of content chunks
            
        Returns:
            Chunks with added relationship context
        """
        enhanced_chunks = []
        
        for chunk in chunks:
            entity_id = chunk["metadata"].get("entity_id")
            if not entity_id:
                enhanced_chunks.append(chunk)
                continue
            
            # Get relationships for this entity
            relationships = self._get_relationship_for_entity(entity_id)
            if not relationships:
                enhanced_chunks.append(chunk)
                continue
            
            # Add relationship context to metadata
            enhanced_chunk = chunk.copy()
            enhanced_chunk["metadata"]["relationships"] = relationships
            
            # Add relationship context to text for better embedding
            relationship_text = "\nRelated components:\n"
            for rel in relationships:
                if rel["direction"] == "outgoing":
                    relationship_text += f"- {rel['relation_type']} {rel['target_name']} ({rel['target_type']})\n"
                else:
                    relationship_text += f"- {rel['source_name']} ({rel['source_type']}) {rel['relation_type']} this\n"
            
            enhanced_chunk["text"] = enhanced_chunk["text"] + relationship_text
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def _process_api_docs(self) -> List[Dict]:
        """Process API documentation."""
        logger.info("Processing API documentation...")
        api_dir = self.input_dir / "api"
        chunks = []
        
        if not api_dir.exists():
            logger.warning(f"API directory not found: {api_dir}")
            return chunks
        
        # Process each API documentation file
        for file_path in tqdm(list(api_dir.glob("*.json"))):
            try:
                with open(file_path, "r") as f:
                    doc = json.load(f)
                
                # Prepare metadata
                metadata = {
                    "id": doc.get("id", file_path.stem),
                    "title": doc.get("title", file_path.stem),
                    "type": "api",
                    "entity_id": doc.get("id", file_path.stem),
                    "category": doc.get("metadata", {}).get("category", "general"),
                    "version": doc.get("metadata", {}).get("version", "unknown"),
                    "filename": file_path.name,
                    "tags": doc.get("metadata", {}).get("tags", [])
                }
                
                # Prepare text content
                content = doc.get("content", "")
                if isinstance(content, dict):
                    # If content is a complex structure, convert to text
                    content_text = json.dumps(content, indent=2)
                else:
                    content_text = str(content)
                
                # Create a header with important metadata
                header = f"{metadata['title']}\n"
                header += f"Type: API Documentation\n"
                header += f"Category: {metadata['category']}\n"
                header += f"Version: {metadata['version']}\n"
                if metadata.get("tags"):
                    header += f"Tags: {', '.join(metadata['tags'])}\n"
                header += "\n"
                
                # Combine header and content
                full_text = header + content_text
                
                # Chunk the content
                doc_chunks = self._chunk_text(full_text, metadata)
                chunks.extend(doc_chunks)
                
                self.api_chunks += len(doc_chunks)
                
            except Exception as e:
                logger.error(f"Failed to process API file {file_path}: {e}")
        
        logger.info(f"Created {len(chunks)} API chunks")
        return chunks
    
    def _process_database_docs(self) -> List[Dict]:
        """Process database documentation."""
        logger.info("Processing database documentation...")
        db_dir = self.input_dir / "database"
        chunks = []
        
        if not db_dir.exists():
            logger.warning(f"Database directory not found: {db_dir}")
            return chunks
        
        # Process each database documentation file
        for file_path in tqdm(list(db_dir.glob("*.json"))):
            try:
                with open(file_path, "r") as f:
                    doc = json.load(f)
                
                # Prepare metadata
                metadata = {
                    "id": doc.get("id", file_path.stem),
                    "title": doc.get("title", file_path.stem),
                    "type": "database",
                    "entity_id": doc.get("id", file_path.stem),
                    "database": doc.get("metadata", {}).get("database", "main"),
                    "table": doc.get("metadata", {}).get("table", file_path.stem),
                    "filename": file_path.name,
                    "tags": doc.get("metadata", {}).get("tags", [])
                }
                
                # Prepare text content
                content = doc.get("content", "")
                if isinstance(content, dict):
                    # If content is a complex structure, convert to text
                    content_text = ""
                    
                    # Handle database schema structure
                    if "columns" in content:
                        content_text += f"Table: {metadata['table']}\n\n"
                        content_text += "Columns:\n"
                        
                        for column in content["columns"]:
                            col_name = column.get("name", "unknown")
                            col_type = column.get("type", "unknown")
                            col_desc = column.get("description", "")
                            col_required = "Required" if column.get("required") else "Optional"
                            
                            content_text += f"- {col_name} ({col_type}, {col_required}): {col_desc}\n"
                        
                        content_text += "\n"
                    
                    if "indexes" in content:
                        content_text += "Indexes:\n"
                        
                        for index in content["indexes"]:
                            idx_name = index.get("name", "unknown")
                            idx_columns = ", ".join(index.get("columns", []))
                            idx_type = index.get("type", "normal")
                            
                            content_text += f"- {idx_name} ({idx_type}): {idx_columns}\n"
                        
                        content_text += "\n"
                    
                    if "relationships" in content:
                        content_text += "Relationships:\n"
                        
                        for rel in content["relationships"]:
                            rel_type = rel.get("type", "unknown")
                            rel_target = rel.get("target_table", "unknown")
                            rel_columns = ", ".join(rel.get("columns", []))
                            rel_target_columns = ", ".join(rel.get("target_columns", []))
                            
                            content_text += f"- {rel_type} to {rel_target}: {rel_columns} -> {rel_target_columns}\n"
                        
                        content_text += "\n"
                    
                    # If there's additional content not handled above
                    if not content_text:
                        content_text = json.dumps(content, indent=2)
                else:
                    content_text = str(content)
                
                # Create a header with important metadata
                header = f"{metadata['title']}\n"
                header += f"Type: Database Documentation\n"
                header += f"Database: {metadata['database']}\n"
                header += f"Table: {metadata['table']}\n"
                if metadata.get("tags"):
                    header += f"Tags: {', '.join(metadata['tags'])}\n"
                header += "\n"
                
                # Combine header and content
                full_text = header + content_text
                
                # Chunk the content
                doc_chunks = self._chunk_text(full_text, metadata)
                chunks.extend(doc_chunks)
                
                self.database_chunks += len(doc_chunks)
                
            except Exception as e:
                logger.error(f"Failed to process database file {file_path}: {e}")
        
        logger.info(f"Created {len(chunks)} database chunks")
        return chunks
    
    def _process_manual_docs(self) -> List[Dict]:
        """Process user manual documentation."""
        logger.info("Processing manual documentation...")
        manual_dir = self.input_dir / "manual"
        chunks = []
        
        if not manual_dir.exists():
            logger.warning(f"Manual directory not found: {manual_dir}")
            return chunks
        
        # Process each manual documentation file
        for file_path in tqdm(list(manual_dir.glob("*.json"))):
            try:
                with open(file_path, "r") as f:
                    doc = json.load(f)
                
                # Prepare metadata
                metadata = {
                    "id": doc.get("id", file_path.stem),
                    "title": doc.get("title", file_path.stem),
                    "type": "manual",
                    "entity_id": doc.get("id", file_path.stem),
                    "section": doc.get("metadata", {}).get("section", "general"),
                    "chapter": doc.get("metadata", {}).get("chapter", "general"),
                    "filename": file_path.name,
                    "tags": doc.get("metadata", {}).get("tags", [])
                }
                
                # Prepare text content
                content = doc.get("content", "")
                if isinstance(content, dict):
                    # If content is a complex structure, convert to text
                    content_text = json.dumps(content, indent=2)
                else:
                    content_text = str(content)
                
                # Create a header with important metadata
                header = f"{metadata['title']}\n"
                header += f"Type: User Manual\n"
                header += f"Section: {metadata['section']}\n"
                header += f"Chapter: {metadata['chapter']}\n"
                if metadata.get("tags"):
                    header += f"Tags: {', '.join(metadata['tags'])}\n"
                header += "\n"
                
                # Combine header and content
                full_text = header + content_text
                
                # Chunk the content
                doc_chunks = self._chunk_text(full_text, metadata)
                chunks.extend(doc_chunks)
                
                self.manual_chunks += len(doc_chunks)
                
            except Exception as e:
                logger.error(f"Failed to process manual file {file_path}: {e}")
        
        logger.info(f"Created {len(chunks)} manual chunks")
        return chunks
    
    def _create_relationship_embeddings(self) -> List[Dict]:
        """Create specific embeddings for relationships."""
        logger.info("Creating relationship embeddings...")
        chunks = []
        
        if not self.relationships.get("edges"):
            logger.warning("No relationships found")
            return chunks
        
        # Process each relationship
        for edge in tqdm(self.relationships.get("edges", [])):
            try:
                source_id = edge.get("source")
                target_id = edge.get("target")
                relation_type = edge.get("type", "related_to")
                
                # Get the node information
                source_node = next((node for node in self.relationships.get("nodes", []) 
                                   if node.get("id") == source_id), {})
                target_node = next((node for node in self.relationships.get("nodes", []) 
                                   if node.get("id") == target_id), {})
                
                source_name = source_node.get("name", "Unknown")
                source_type = source_node.get("type", "Unknown")
                target_name = target_node.get("name", "Unknown")
                target_type = target_node.get("type", "Unknown")
                
                # Create a unique ID for this relationship
                rel_id = f"rel_{source_id}_{target_id}_{relation_type}"
                
                # Prepare metadata
                metadata = {
                    "id": rel_id,
                    "title": f"Relationship: {source_name} {relation_type} {target_name}",
                    "type": "relationship",
                    "relation_type": relation_type,
                    "source_id": source_id,
                    "source_name": source_name,
                    "source_type": source_type,
                    "target_id": target_id,
                    "target_name": target_name,
                    "target_type": target_type
                }
                
                # Create relationship text
                text = f"Relationship: {source_name} ({source_type}) {relation_type} {target_name} ({target_type})\n\n"
                
                # Add source description if available
                if source_node.get("description"):
                    text += f"Source ({source_name}) description: {source_node['description']}\n\n"
                
                # Add target description if available
                if target_node.get("description"):
                    text += f"Target ({target_name}) description: {target_node['description']}\n\n"
                
                # Add relationship description if available
                if edge.get("description"):
                    text += f"Relationship description: {edge['description']}\n\n"
                
                # Add properties if available
                if edge.get("properties"):
                    text += "Relationship properties:\n"
                    for key, value in edge["properties"].items():
                        text += f"- {key}: {value}\n"
                
                # Create a chunk
                chunk = {
                    "id": rel_id,
                    "text": text,
                    "metadata": metadata
                }
                
                chunks.append(chunk)
                
            except Exception as e:
                logger.error(f"Failed to process relationship {edge.get('source', 'unknown')}-{edge.get('target', 'unknown')}: {e}")
        
        self.relationship_chunks = len(chunks)
        logger.info(f"Created {len(chunks)} relationship chunks")
        return chunks
    
    def _save_chunk(self, chunk: Dict):
        """Save a chunk to a file."""
        chunk_id = chunk["id"]
        filename = f"{chunk_id}.json"
        file_path = self.chunks_dir / filename
        
        with open(file_path, "w") as f:
            json.dump(chunk, f, indent=2)
    
    def _save_combined_chunks(self, chunks: List[Dict]):
        """Save all chunks to a combined file."""
        output_file = self.output_dir / "embedding_chunks.json"
        
        with open(output_file, "w") as f:
            json.dump({"chunks": chunks}, f, indent=2)
        
        logger.info(f"Saved combined chunks to {output_file}")
    
    def _save_stats(self):
        """Save processing statistics."""
        stats = {
            "timestamp": time.time(),
            "total_chunks": self.total_chunks,
            "api_chunks": self.api_chunks,
            "database_chunks": self.database_chunks,
            "manual_chunks": self.manual_chunks,
            "relationship_chunks": self.relationship_chunks,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }
        
        stats_dir = self.output_dir / "stats"
        os.makedirs(stats_dir, exist_ok=True)
        
        stats_file = stats_dir / f"embedding_stats_{int(time.time())}.json"
        
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Saved embedding statistics to {stats_file}")
    
    def process(self):
        """Process all documentation and prepare for embedding."""
        logger.info("Starting embedding preparation...")
        
        # Process documentation
        api_chunks = self._process_api_docs()
        db_chunks = self._process_database_docs()
        manual_chunks = self._process_manual_docs()
        relationship_chunks = self._create_relationship_embeddings()
        
        # Combine all chunks
        all_chunks = api_chunks + db_chunks + manual_chunks + relationship_chunks
        
        # Add relationship context to content chunks
        enhanced_chunks = self._add_relationship_context(all_chunks)
        
        self.total_chunks = len(enhanced_chunks)
        
        # Save individual chunks
        logger.info(f"Saving {self.total_chunks} individual chunks...")
        for chunk in tqdm(enhanced_chunks):
            self._save_chunk(chunk)
        
        # Save combined chunks
        logger.info("Saving combined chunks file...")
        self._save_combined_chunks(enhanced_chunks)
        
        # Save statistics
        self._save_stats()
        
        logger.info("Embedding preparation complete!")
        logger.info(f"Total chunks: {self.total_chunks}")
        logger.info(f"API chunks: {self.api_chunks}")
        logger.info(f"Database chunks: {self.database_chunks}")
        logger.info(f"Manual chunks: {self.manual_chunks}")
        logger.info(f"Relationship chunks: {self.relationship_chunks}")

def main():
    parser = argparse.ArgumentParser(description="Prepare Open Dental documentation for embedding")
    parser.add_argument("--input-dir", required=True, help="Path to the processed documentation directory")
    parser.add_argument("--output-dir", required=True, help="Path to output embedding chunks")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Maximum size of content chunks in characters")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Overlap between chunks in characters")
    
    args = parser.parse_args()
    
    preparer = EmbeddingPreparer(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    
    preparer.process()

if __name__ == "__main__":
    main()
