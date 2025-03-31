#!/usr/bin/env python3
"""
Vector Database Query Tool for Open Dental Documentation
=====================================================

This script provides a CLI interface to query the OpenAI vector database
containing the processed Open Dental documentation.

Usage:
    python query_vector_db.py --openai-api-key YOUR_API_KEY --index-id YOUR_INDEX_ID --query "How to create a patient?"

Requirements:
    - openai>=1.0.0
"""

import argparse
import json
import os
import time
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VectorDBQuery:
    """Query the OpenAI vector database."""
    
    def __init__(self, openai_api_key: str, index_id: str):
        """Initialize the query tool.
        
        Args:
            openai_api_key: OpenAI API key
            index_id: ID of the vector index
        """
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.index_id = index_id
    
    def create_query_embedding(self, query: str) -> List[float]:
        """Create an embedding vector for the query.
        
        Args:
            query: Query string
            
        Returns:
            Embedding vector for the query
        """
        try:
            response = self.openai_client.embeddings.create(
                input=query,
                model="text-embedding-ada-002"
            )
            
            embedding = response.data[0].embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to create query embedding: {e}")
            raise
    
    def query_index(self, query: str, top_k: int = 5) -> List[Dict]:
        """Query the vector index.
        
        Args:
            query: Query string
            top_k: Number of top results to return
            
        Returns:
            List of matching documents with scores
        """
        try:
            # Create query embedding
            query_embedding = self.create_query_embedding(query)
            
            # Search the vector index
            response = self.openai_client.beta.vector_stores.query(
                vector_store_id=self.index_id,
                query_vector=query_embedding,
                k=top_k
            )
            
            # Format results
            results = []
            for i, match in enumerate(response.matches):
                results.append({
                    "rank": i + 1,
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata,
                    "text": match.content
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query vector index: {e}")
            raise
    
    def enhance_results_with_context(self, query: str, results: List[Dict]) -> List[Dict]:
        """Enhance query results with generated context.
        
        Args:
            query: Original query string
            results: Raw search results
            
        Returns:
            Enhanced results with generated context
        """
        enhanced_results = []
        
        for result in results:
            # Prepare a prompt for the model to analyze the result
            prompt = f"""
            Original Query: {query}
            
            Result:
            {result['text']}
            
            Please analyze this result and provide:
            1. How relevant this result is to the query (on a scale of 1-10)
            2. What specific information from this result answers the query
            3. Any additional context needed to understand this result
            """
            
            try:
                # Generate analysis using completion API
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",  # You can use gpt-4 for better analysis
                    messages=[
                        {"role": "system", "content": "You are an expert code documentation assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=250,
                    temperature=0.3
                )
                
                analysis = response.choices[0].message.content
                
                # Add analysis to the result
                enhanced_result = result.copy()
                enhanced_result["analysis"] = analysis.strip()
                enhanced_results.append(enhanced_result)
                
                # Sleep to avoid rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to enhance result {result['id']}: {e}")
                # Still include the original result
                enhanced_results.append(result)
        
        return enhanced_results
    
    def answer_query(self, query: str, top_k: int = 5, enhance: bool = True) -> Dict:
        """Answer a query using the vector index.
        
        Args:
            query: Query string
            top_k: Number of top results to return
            enhance: Whether to enhance results with generated context
            
        Returns:
            Dictionary containing query results and answer
        """
        # Query the vector index
        results = self.query_index(query, top_k)
        
        if not results:
            return {
                "success": False,
                "error": "No results found",
                "query": query,
                "results": []
            }
        
        # Enhance results if requested
        if enhance:
            results = self.enhance_results_with_context(query, results)
        
        # Generate a comprehensive answer
        answer_prompt = f"""
        Original Query: {query}
        
        Search Results:
        {json.dumps([{
            "id": r["id"],
            "metadata": r["metadata"],
            "text": r["text"],
            "analysis": r.get("analysis", "")
        } for r in results], indent=2)}
        
        Based on these search results, provide a comprehensive answer to the original query.
        Include specific references to the documentation where appropriate, and highlight
        any relationships between different components.
        
        If there are any gaps or uncertainties in the information, please note them.
        """
        
        try:
            # Generate answer using completion API
            response = self.openai_client.chat.completions.create(
                model="gpt-4",  # Use the best model available for synthesis
                messages=[
                    {"role": "system", "content": "You are an expert in Open Dental software documentation, specializing in API, database schema, and user manual integration."},
                    {"role": "user", "content": answer_prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "answer": answer.strip()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return {
                "success": False,
                "error": f"Failed to generate answer: {e}",
                "query": query,
                "results": results
            }

def format_output(result: Dict) -> str:
    """Format the query result for display.
    
    Args:
        result: Query result
        
    Returns:
        Formatted output string
    """
    if not result["success"]:
        return f"Error: {result.get('error', 'Unknown error')}"
    
    output = f"Query: {result['query']}\n\n"
    
    output += "Answer:\n"
    output += "=" * 80 + "\n"
    output += result["answer"] + "\n"
    output += "=" * 80 + "\n\n"
    
    output += f"Top {len(result['results'])} Results:\n"
    output += "-" * 80 + "\n"
    
    for i, r in enumerate(result["results"]):
        output += f"Result {i+1} (score: {r['score']:.4f}):\n"
        output += f"ID: {r['id']}\n"
        output += f"Type: {r['metadata'].get('type', 'Unknown')}\n"
        
        # Truncate text for display
        text = r['text']
        if len(text) > 300:
            text = text[:300] + "..."
        
        output += f"Content: {text}\n"
        
        if "analysis" in r:
            output += f"Analysis: {r['analysis']}\n"
        
        output += "-" * 80 + "\n"
    
    return output

def main():
    parser = argparse.ArgumentParser(description="Query the OpenAI vector database containing Open Dental documentation")
    parser.add_argument("--openai-api-key", required=True, help="OpenAI API key")
    parser.add_argument("--index-id", required=True, help="ID of the vector index")
    parser.add_argument("--query", required=True, help="Query string")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top results to return")
    parser.add_argument("--no-enhance", action="store_true", help="Disable result enhancement")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    query_tool = VectorDBQuery(
        openai_api_key=args.openai_api_key,
        index_id=args.index_id
    )
    
    result = query_tool.answer_query(
        query=args.query,
        top_k=args.top_k,
        enhance=not args.no_enhance
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_output(result))

if __name__ == "__main__":
    main()
