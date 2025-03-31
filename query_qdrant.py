from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from openai import OpenAI
import os
import dotenv
import argparse

# Load environment variables from .env file
dotenv.load_dotenv()

# Initialize OpenAI client
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Connect to your local Qdrant instance
client = QdrantClient(host="localhost", port=6333)
collection_name = "open_dental_docs"

def get_embedding(text):
    """Get embedding for a given text using OpenAI API"""
    response = client_openai.embeddings.create(
        input=text,
        model="text-embedding-ada-002"  # Or whatever model you're using
    )
    return response.data[0].embedding

def search_docs(query_text, limit=5, filter_type=None):
    """Search for documents matching the query text"""
    # Get embedding for the query
    query_vector = get_embedding(query_text)
    
    # Set up filter if specified
    search_filter = None
    if filter_type:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="type",
                    match=MatchValue(value=filter_type)
                )
            ]
        )
    
    # Perform the search
    search_result = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        filter=search_filter
    )
    
    return search_result

def print_results(results):
    """Pretty print the search results"""
    print("\n=== SEARCH RESULTS ===\n")
    for i, result in enumerate(results):
        print(f"Result {i+1} (Score: {result.score:.4f}):")
        print(f"Type: {result.payload.get('type', 'Unknown')}")
        print(f"Title: {result.payload.get('title', 'Untitled')}")
        print(f"Text: {result.payload.get('text', '')[:300]}...")
        print("-" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query Open Dental documentation")
    parser.add_argument("query", help="The query text to search for")
    parser.add_argument("--limit", type=int, default=5, help="Number of results to return")
    parser.add_argument("--filter", choices=["api", "database", "manual", "relationship"], 
                        help="Filter by document type")
    
    args = parser.parse_args()
    
    results = search_docs(args.query, args.limit, args.filter)
    print_results(results)