#!/usr/bin/env python3
"""
Local Embeddings Generator for Open Dental Documentation
=====================================================

This script generates embeddings for the processed Open Dental documentation and
saves them locally in a format that can be easily imported into vector databases.

Usage:
    python prepare_local_embeddings.py --input-dir /path/to/processed/docs --output-dir /path/to/output

Environment Variables:
    - OPENAI_API_KEY: Your OpenAI API key

Requirements:
    - openai>=1.0.0
    - tqdm
    - dotenv
"""

import argparse
import json
import os
import sys
import time
import hashlib
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional, Set
import openai
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

class LocalEmbeddingsGenerator:
    """Generate and save embeddings locally for use with any vector database."""
    
    def __init__(self, input_dir: str, output_dir: str, batch_size: int = 100, force_refresh: bool = False):
        """Initialize the generator.
        
        Args:
            input_dir: Directory containing processed documentation
            output_dir: Directory to save embeddings
            batch_size: Number of items to embed in a single batch
            force_refresh: Force refresh all embeddings even if they exist
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        
        self.openai_client = openai.OpenAI(api_key=self.api_key)
        self.batch_size = batch_size
        self.force_refresh = force_refresh
        self.metadata_file = self.output_dir / "metadata.json"
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.output_dir / "api", exist_ok=True)
        os.makedirs(self.output_dir / "database", exist_ok=True)
        os.makedirs(self.output_dir / "manual", exist_ok=True)
        os.makedirs(self.output_dir / "relationship", exist_ok=True)
        os.makedirs(self.output_dir / "stats", exist_ok=True)
    
    def load_chunk_metadata(self) -> Dict[str, Dict]:
        """Load metadata about previously processed chunks.
        
        Returns:
            Dictionary mapping chunk IDs to metadata about the chunk
        """
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata file: {e}")
            return {}
    
    def save_chunk_metadata(self, metadata: Dict[str, Dict]) -> None:
        """Save metadata about processed chunks.
        
        Args:
            metadata: Dictionary mapping chunk IDs to metadata
        """
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata file: {e}")
    
    def compute_chunk_hash(self, chunk: Dict) -> str:
        """Compute a hash for a chunk to detect changes.
        
        Args:
            chunk: Chunk to hash
            
        Returns:
            Hash of the chunk content
        """
        # Create a hash based on the text and metadata
        # This will allow us to detect if the chunk content has changed
        content_str = chunk["text"] + json.dumps(chunk["metadata"], sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def load_chunks(self) -> List[Dict]:
        """Load all chunks from the input directory."""
        logger.info("Loading embedding chunks...")
        
        # Try to load from the combined file first
        combined_file = self.input_dir / "embedding_chunks.json"
        if combined_file.exists():
            try:
                with open(combined_file, "r") as f:
                    data = json.load(f)
                    chunks = data.get("chunks", [])
                    logger.info(f"Loaded {len(chunks)} chunks from combined file")
                    return chunks
            except Exception as e:
                logger.error(f"Failed to load combined file: {e}")
        
        # Fall back to loading individual chunk files
        chunks = []
        chunks_dir = self.input_dir / "chunks"
        if chunks_dir.exists():
            for file_path in chunks_dir.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        chunk = json.load(f)
                        chunks.append(chunk)
                except Exception as e:
                    logger.error(f"Failed to load chunk {file_path}: {e}")
            
            logger.info(f"Loaded {len(chunks)} individual chunk files")
        
        return chunks
    
    def filter_new_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Filter out chunks that haven't changed since last processing.
        
        Args:
            chunks: List of chunks to filter
            
        Returns:
            List of chunks that are new or have changed
        """
        if self.force_refresh:
            logger.info("Force refresh enabled - processing all chunks")
            return chunks
        
        existing_metadata = self.load_chunk_metadata()
        new_chunks = []
        
        for chunk in chunks:
            chunk_id = chunk["id"]
            chunk_hash = self.compute_chunk_hash(chunk)
            
            # Check if this chunk exists and has the same hash
            if chunk_id in existing_metadata and existing_metadata[chunk_id]["hash"] == chunk_hash:
                continue
            
            new_chunks.append(chunk)
        
        logger.info(f"Found {len(new_chunks)} new or modified chunks out of {len(chunks)} total chunks")
        return new_chunks
    
    def create_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """Create embeddings for chunks.
        
        Args:
            chunks: List of chunks to embed
            
        Returns:
            List of chunks with embeddings
        """
        if not chunks:
            logger.info("No new chunks to embed")
            return []
            
        logger.info("Creating embeddings...")
        chunks_with_embeddings = []
        
        # Process in batches to avoid API rate limits
        for i in tqdm(range(0, len(chunks), self.batch_size)):
            batch = chunks[i:i + self.batch_size]
            texts = [chunk["text"] for chunk in batch]
            
            try:
                response = self.openai_client.embeddings.create(
                    input=texts,
                    model="text-embedding-ada-002"  # Can be changed to newer models
                )
                
                embedding_vectors = response.data
                
                for j, chunk in enumerate(batch):
                    chunk_with_embedding = chunk.copy()
                    chunk_with_embedding["embedding"] = embedding_vectors[j].embedding
                    chunks_with_embeddings.append(chunk_with_embedding)
                
                # Sleep to avoid rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to create embeddings for batch starting at index {i}: {e}")
                # Skip this batch and continue with the next one
                continue
        
        logger.info(f"Created embeddings for {len(chunks_with_embeddings)} chunks")
        return chunks_with_embeddings
    
    def load_existing_embeddings(self) -> List[Dict]:
        """Load existing embeddings from the output directory.
        
        Returns:
            List of chunks with embeddings
        """
        if self.force_refresh:
            return []
            
        # Check if the combined file exists
        combined_file = self.output_dir / "combined_embeddings.json"
        if combined_file.exists():
            try:
                with open(combined_file, "r") as f:
                    data = json.load(f)
                    existing_chunks = data.get("chunks", [])
                    logger.info(f"Loaded {len(existing_chunks)} existing chunks from combined file")
                    return existing_chunks
            except Exception as e:
                logger.error(f"Failed to load existing combined file: {e}")
        
        return []
    
    def save_embeddings(self, new_chunks_with_embeddings: List[Dict]) -> Dict:
        """Save embeddings to files based on their type.
        
        Args:
            new_chunks_with_embeddings: List of new chunks with embeddings
            
        Returns:
            Dictionary with statistics
        """
        # Load existing chunks if available
        existing_chunks = self.load_existing_embeddings()
        
        # Combine existing chunks with new chunks, replacing any duplicates
        all_chunks = existing_chunks.copy()
        
        # Create a dictionary of existing chunks by ID for quick lookup
        existing_chunks_by_id = {chunk["id"]: i for i, chunk in enumerate(all_chunks)}
        
        # Add or replace chunks
        for chunk in new_chunks_with_embeddings:
            chunk_id = chunk["id"]
            if chunk_id in existing_chunks_by_id:
                # Replace existing chunk
                all_chunks[existing_chunks_by_id[chunk_id]] = chunk
            else:
                # Add new chunk
                all_chunks.append(chunk)
        
        logger.info(f"Saving {len(all_chunks)} embeddings ({len(new_chunks_with_embeddings)} new or updated)...")
        
        # Initialize counters
        stats = {
            "total": len(all_chunks),
            "api": 0,
            "database": 0,
            "manual": 0,
            "relationship": 0,
            "timestamp": time.time(),
            "new_or_updated": len(new_chunks_with_embeddings)
        }
        
        # Track processed chunk metadata
        chunk_metadata = self.load_chunk_metadata()
        
        # Group chunks by type and save individual files
        for chunk in tqdm(all_chunks):
            chunk_type = chunk["metadata"].get("type", "unknown")
            chunk_id = chunk["id"]
            
            # Update metadata with chunk hash
            chunk_metadata[chunk_id] = {
                "hash": self.compute_chunk_hash(chunk),
                "last_processed": time.time(),
                "type": chunk_type
            }
            
            # Determine the appropriate directory
            if chunk_type == "api":
                output_dir = self.output_dir / "api"
                stats["api"] += 1
            elif chunk_type == "database":
                output_dir = self.output_dir / "database"
                stats["database"] += 1
            elif chunk_type == "manual":
                output_dir = self.output_dir / "manual"
                stats["manual"] += 1
            elif chunk_type == "relationship":
                output_dir = self.output_dir / "relationship"
                stats["relationship"] += 1
            else:
                output_dir = self.output_dir
            
            # Save the chunk with embedding
            with open(output_dir / f"{chunk_id}.json", "w") as f:
                json.dump(chunk, f, indent=2)
        
        # Save combined file
        with open(self.output_dir / "combined_embeddings.json", "w") as f:
            json.dump({"chunks": all_chunks}, f)
        
        # Save metadata
        self.save_chunk_metadata(chunk_metadata)
        
        # Save stats
        stats_file = self.output_dir / "stats" / f"embeddings_stats_{int(time.time())}.json"
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Saved embeddings and stats to {self.output_dir}")
        return stats
    
    def process(self) -> Dict:
        """Process all documentation and generate embeddings.
        
        Returns:
            Dictionary with statistics
        """
        # Load chunks
        chunks = self.load_chunks()
        
        if not chunks:
            logger.error("No chunks found to process")
            return {"success": False, "error": "No chunks found"}
        
        # Filter out chunks that haven't changed
        new_chunks = self.filter_new_chunks(chunks)
        
        if not new_chunks and not self.force_refresh:
            logger.info("No new or modified chunks to process")
            return {
                "success": True, 
                "stats": {
                    "total": len(chunks),
                    "new_or_updated": 0
                }
            }
        
        # Create embeddings for new or modified chunks
        new_chunks_with_embeddings = self.create_embeddings(new_chunks)
        
        # Save embeddings (combining with existing embeddings)
        stats = self.save_embeddings(new_chunks_with_embeddings)
        
        return {
            "success": True,
            "stats": stats
        }

def main():
    parser = argparse.ArgumentParser(description="Generate and save embeddings locally")
    parser.add_argument("--input-dir", required=True, help="Path to directory containing processed documentation")
    parser.add_argument("--output-dir", required=True, help="Path to directory to save embeddings")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of items to embed in a single batch")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh all embeddings")
    
    args = parser.parse_args()
    
    generator = LocalEmbeddingsGenerator(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        force_refresh=args.force_refresh
    )
    
    result = generator.process()
    
    if result["success"]:
        print(f"Successfully processed embeddings!")
        stats = result["stats"]
        print(f"Total chunks: {stats['total']}")
        if "new_or_updated" in stats:
            print(f"New or updated chunks: {stats['new_or_updated']}")
        if "api" in stats:
            print(f"API chunks: {stats['api']}")
            print(f"Database chunks: {stats['database']}")
            print(f"Manual chunks: {stats['manual']}")
            print(f"Relationship chunks: {stats['relationship']}")
        sys.exit(0)
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
