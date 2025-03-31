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
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional
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
    
    def __init__(self, input_dir: str, output_dir: str, batch_size: int = 100):
        """Initialize the generator.
        
        Args:
            input_dir: Directory containing processed documentation
            output_dir: Directory to save embeddings
            batch_size: Number of items to embed in a single batch
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        
        self.openai_client = openai.OpenAI(api_key=self.api_key)
        self.batch_size = batch_size
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.output_dir / "api", exist_ok=True)
        os.makedirs(self.output_dir / "database", exist_ok=True)
        os.makedirs(self.output_dir / "manual", exist_ok=True)
        os.makedirs(self.output_dir / "relationship", exist_ok=True)
        os.makedirs(self.output_dir / "stats", exist_ok=True)
    
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
    
    def create_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """Create embeddings for chunks.
        
        Args:
            chunks: List of chunks to embed
            
        Returns:
            List of chunks with embeddings
        """
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
    
    def save_embeddings(self, chunks_with_embeddings: List[Dict]) -> Dict:
        """Save embeddings to files based on their type.
        
        Args:
            chunks_with_embeddings: List of chunks with embeddings
            
        Returns:
            Dictionary with statistics
        """
        logger.info("Saving embeddings...")
        
        # Initialize counters
        stats = {
            "total": len(chunks_with_embeddings),
            "api": 0,
            "database": 0,
            "manual": 0,
            "relationship": 0,
            "timestamp": time.time()
        }
        
        # Group chunks by type
        for chunk in tqdm(chunks_with_embeddings):
            chunk_type = chunk["metadata"].get("type", "unknown")
            
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
            chunk_id = chunk["id"]
            with open(output_dir / f"{chunk_id}.json", "w") as f:
                json.dump(chunk, f, indent=2)
        
        # Save combined file
        with open(self.output_dir / "combined_embeddings.json", "w") as f:
            json.dump({"chunks": chunks_with_embeddings}, f)
        
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
        
        # Create embeddings
        chunks_with_embeddings = self.create_embeddings(chunks)
        
        if not chunks_with_embeddings:
            logger.error("Failed to create embeddings")
            return {"success": False, "error": "Failed to create embeddings"}
        
        # Save embeddings
        stats = self.save_embeddings(chunks_with_embeddings)
        
        return {
            "success": True,
            "stats": stats
        }

def main():
    parser = argparse.ArgumentParser(description="Generate and save embeddings locally")
    parser.add_argument("--input-dir", required=True, help="Path to directory containing processed documentation")
    parser.add_argument("--output-dir", required=True, help="Path to directory to save embeddings")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of items to embed in a single batch")
    
    args = parser.parse_args()
    
    generator = LocalEmbeddingsGenerator(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size
    )
    
    result = generator.process()
    
    if result["success"]:
        print(f"Successfully created and saved embeddings!")
        stats = result["stats"]
        print(f"Total chunks: {stats['total']}")
        print(f"API chunks: {stats['api']}")
        print(f"Database chunks: {stats['database']}")
        print(f"Manual chunks: {stats['manual']}")
        print(f"Relationship chunks: {stats['relationship']}")
    else:
        print(f"Failed to create embeddings: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
