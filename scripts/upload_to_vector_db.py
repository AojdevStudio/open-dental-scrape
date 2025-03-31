#!/usr/bin/env python3
"""
Vector Database Uploader for Open Dental Documentation
=====================================================

This script takes the processed embedding chunks from the prepare_code_embeddings.py
script and uploads them to an OpenAI vector database.

Usage:
    python upload_to_vector_db.py --input-dir /path/to/processed/embeddings [--openai-api-key YOUR_API_KEY]

Environment Variables:
    - OPENAI_API_KEY: Your OpenAI API key (alternative to --openai-api-key)
    - VECTOR_INDEX_NAME: Name of the vector index (alternative to --index-name)
    - VECTOR_INDEX_DESCRIPTION: Description of the vector index (alternative to --index-description)

Requirements:
    - openai>=1.0.0
    - tqdm
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

class VectorDBUploader:
    """Upload processed embedding chunks to an OpenAI vector database."""
    
    def __init__(self, input_dir: str, openai_api_key: str, batch_size: int = 100):
        """Initialize the uploader.
        
        Args:
            input_dir: Directory containing processed embedding chunks
            openai_api_key: OpenAI API key
            batch_size: Number of chunks to upload in a single batch
        """
        self.input_dir = Path(input_dir)
        self.chunks_dir = self.input_dir / "chunks"
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.batch_size = batch_size
        
        # Create stats directory
        (self.input_dir / "stats").mkdir(exist_ok=True)
    
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
        if self.chunks_dir.exists():
            for file_path in self.chunks_dir.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        chunk = json.load(f)
                        chunks.append(chunk)
                except Exception as e:
                    logger.error(f"Failed to load chunk {file_path}: {e}")
            
            logger.info(f"Loaded {len(chunks)} individual chunk files")
        
        return chunks
    
    def _create_embedding_vectors(self, chunks: List[Dict]) -> List[Dict]:
        """Create embedding vectors for chunks using OpenAI API.
        
        Args:
            chunks: List of embedding chunks
            
        Returns:
            List of chunks with embedding vectors added
        """
        logger.info("Creating embedding vectors...")
        chunks_with_vectors = []
        
        # Process in batches to avoid API rate limits
        for i in tqdm(range(0, len(chunks), self.batch_size)):
            batch = chunks[i:i + self.batch_size]
            texts = [chunk["text"] for chunk in batch]
            
            try:
                response = self.openai_client.embeddings.create(
                    input=texts,
                    model="text-embedding-ada-002"  # You can change this to a different model if needed
                )
                
                embedding_vectors = response.data
                
                for j, chunk in enumerate(batch):
                    chunk_with_vector = chunk.copy()
                    chunk_with_vector["embedding"] = embedding_vectors[j].embedding
                    chunks_with_vectors.append(chunk_with_vector)
                
                # Sleep to avoid rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to create embeddings for batch starting at index {i}: {e}")
                # Skip this batch and continue with the next one
                continue
        
        logger.info(f"Created embeddings for {len(chunks_with_vectors)} chunks")
        return chunks_with_vectors
    
    def _create_vector_index(self, name: str, description: str) -> str:
        """Create a new vector index in OpenAI.
        
        Args:
            name: Name of the vector index
            description: Description of the vector index
            
        Returns:
            ID of the created vector index
        """
        logger.info(f"Creating vector index: {name}")
        
        try:
            # In the current OpenAI API, vector indexes are created differently
            # We'll use the Files API to create and upload vectors
            
            # First, create a temporary file with our vectors
            temp_file_path = self.input_dir / "temp_vectors.jsonl"
            with open(temp_file_path, "w") as f:
                f.write(json.dumps({
                    "name": name,
                    "description": description,
                    "metadata": {
                        "embedding_model": "text-embedding-ada-002"
                    }
                }))
            
            # Upload the file to OpenAI
            with open(temp_file_path, "rb") as file:
                response = self.openai_client.files.create(
                    file=file,
                    purpose="vector_index"
                )
            
            # Clean up
            if temp_file_path.exists():
                temp_file_path.unlink()
            
            index_id = response.id
            logger.info(f"Created vector index with ID: {index_id}")
            
            return index_id
            
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            raise
    
    def _upload_to_vector_index(self, index_id: str, chunks_with_vectors: List[Dict]) -> int:
        """Upload chunks with embedding vectors to the OpenAI vector index.
        
        Args:
            index_id: ID of the vector index
            chunks_with_vectors: List of chunks with embedding vectors
            
        Returns:
            Number of successfully uploaded chunks
        """
        logger.info(f"Uploading {len(chunks_with_vectors)} chunks to vector index: {index_id}")
        
        uploaded_count = 0
        
        # Process in batches to avoid API rate limits
        for i in tqdm(range(0, len(chunks_with_vectors), self.batch_size)):
            batch = chunks_with_vectors[i:i + self.batch_size]
            
            # Prepare data in the format expected by the API
            batch_data = []
            for chunk in batch:
                item = {
                    "id": chunk["id"],
                    "embedding": chunk["embedding"],
                    "metadata": chunk["metadata"],
                    "content": chunk["text"]
                }
                batch_data.append(item)
            
            try:
                # In the current API, vectors are uploaded via files API
                # Create a temporary JSONL file with our vectors
                temp_file_path = self.input_dir / f"temp_vectors_batch_{i}.jsonl"
                with open(temp_file_path, "w") as f:
                    for item in batch_data:
                        f.write(json.dumps(item) + "\n")
                
                # Upload the file to OpenAI
                with open(temp_file_path, "rb") as file:
                    response = self.openai_client.files.create(
                        file=file,
                        purpose="vectors",
                        user_provided_filename=f"batch_{i}.jsonl"
                    )
                    
                    # Attach the file to the vector index
                    self.openai_client.files.attach(
                        file_id=response.id,
                        target_id=index_id,
                        purpose="vector_index"
                    )
                
                # Clean up
                if temp_file_path.exists():
                    temp_file_path.unlink()
                
                # Count successful uploads
                uploaded_count += len(batch)
                
                # Sleep to avoid rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to upload batch starting at index {i}: {e}")
                # Skip this batch and continue with the next one
                continue
        
        logger.info(f"Successfully uploaded {uploaded_count} chunks to vector index")
        return uploaded_count
    
    def _save_upload_stats(self, stats: Dict):
        """Save upload statistics to a file.
        
        Args:
            stats: Dictionary containing upload statistics
        """
        stats_file = self.input_dir / "stats" / f"upload_stats_{int(time.time())}.json"
        
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
            
        logger.info(f"Saved upload statistics to {stats_file}")
    
    def upload(self, index_name: str, index_description: str) -> Dict:
        """Upload embedding chunks to the OpenAI vector database.
        
        Args:
            index_name: Name of the vector index
            index_description: Description of the vector index
            
        Returns:
            Dictionary containing upload statistics
        """
        # Load chunks
        chunks = self.load_chunks()
        
        if not chunks:
            logger.error("No chunks found to upload")
            return {"success": False, "error": "No chunks found"}
        
        # Create embedding vectors
        chunks_with_vectors = self._create_embedding_vectors(chunks)
        
        if not chunks_with_vectors:
            logger.error("Failed to create embedding vectors")
            return {"success": False, "error": "Failed to create embedding vectors"}
        
        # Create vector index
        try:
            index_id = self._create_vector_index(index_name, index_description)
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            return {"success": False, "error": f"Failed to create vector index: {e}"}
        
        # Upload chunks to vector index
        uploaded_count = self._upload_to_vector_index(index_id, chunks_with_vectors)
        
        # Save upload statistics
        stats = {
            "timestamp": time.time(),
            "index_name": index_name,
            "index_id": index_id,
            "total_chunks": len(chunks),
            "uploaded_chunks": uploaded_count,
            "success_rate": uploaded_count / len(chunks) if chunks else 0
        }
        
        self._save_upload_stats(stats)
        
        return {
            "success": True,
            "index_id": index_id,
            "total_chunks": len(chunks),
            "uploaded_chunks": uploaded_count,
            "success_rate": uploaded_count / len(chunks) if chunks else 0
        }

def main():
    parser = argparse.ArgumentParser(description="Upload processed embedding chunks to an OpenAI vector database")
    parser.add_argument("--input-dir", required=True, help="Path to directory containing processed embedding chunks")
    parser.add_argument("--openai-api-key", help="OpenAI API key (can also be set via OPENAI_API_KEY env variable)")
    parser.add_argument("--index-name", help="Name of the vector index (can also be set via VECTOR_INDEX_NAME env variable)")
    parser.add_argument("--index-description", help="Description of the vector index (can also be set via VECTOR_INDEX_DESCRIPTION env variable)")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of chunks to upload in a single batch")
    
    args = parser.parse_args()
    
    # Use environment variables if arguments are not provided
    api_key = args.openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not provided. Set via --openai-api-key or OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    index_name = args.index_name or os.environ.get("VECTOR_INDEX_NAME", "open_dental_docs")
    index_description = args.index_description or os.environ.get(
        "VECTOR_INDEX_DESCRIPTION", "Open Dental documentation for code understanding"
    )
    
    uploader = VectorDBUploader(
        input_dir=args.input_dir,
        openai_api_key=api_key,
        batch_size=args.batch_size
    )
    
    result = uploader.upload(index_name, index_description)
    
    if result["success"]:
        print(f"Successfully uploaded {result['uploaded_chunks']} out of {result['total_chunks']} chunks")
        print(f"Vector index ID: {result['index_id']}")
        print(f"Success rate: {result['success_rate'] * 100:.2f}%")
    else:
        print(f"Upload failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
