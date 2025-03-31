from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from openai import OpenAI
import os
import dotenv
import argparse

# Load environment variables from .env file
dotenv.load_dotenv()

# Set API key - uncomment one of these options:
# Option 1: From .env file
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Option 2: Hardcoded (for testing only)
# client_openai = OpenAI(api_key="your_actual_api_key_here")

# Connect to your local Qdrant instance
qdrant_url = os.getenv("QDRANT_HOST")
if qdrant_url and (qdrant_url.startswith("http://") or qdrant_url.startswith("https://")):
    qdrant_client = QdrantClient(url=qdrant_url)
else:
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_client = QdrantClient(host="localhost", port=qdrant_port)

collection_name = "open_dental_docs"

def get_embedding(text):
    """Get embedding for a given text using OpenAI API (new format)"""
    response = client_openai.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
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
    
    # Create search params - only add filter if it's specified
    search_params = {
        "collection_name": collection_name,
        "query": query_vector,
        "limit": limit,
        "with_payload": True,
        "with_vectors": False
    }
    
    if search_filter:
        search_params["query_filter"] = search_filter
    
    # Perform the search using query_points instead of search
    response = qdrant_client.query_points(**search_params)
    return response.points  # Return just the points from the response

def print_results(results):
    """Pretty print the search results"""
    print("\n=== SEARCH RESULTS ===\n")
    
    if not results:
        print("No results found. This could indicate an issue with the collection.")
        return
        
    for i, result in enumerate(results):
        print(f"Result {i+1} (Score: {result.score:.4f}):")
        print(f"Original ID: {result.payload.get('original_id', 'Unknown')}")
        print(f"Type: {result.payload.get('type', 'Unknown')}")
        print(f"Title: {result.payload.get('title', 'Untitled')}")
        text = result.payload.get('text', '')
        # Try to find the most relevant part of the text
        lines = text.split('\n')
        relevant_lines = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['create', 'add', 'new', 'post', 'put', 'insert']):
                relevant_lines.append(line)
        
        if relevant_lines:
            print("Relevant text:")
            for line in relevant_lines[:3]:  # Show up to 3 most relevant lines
                print(f"  {line.strip()}")
        else:
            print(f"Text snippet: {text[:300]}...")
        print("-" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query Open Dental documentation")
    parser.add_argument("query", help="The query text to search for")
    parser.add_argument("--limit", type=int, default=5, help="Number of results to return")
    parser.add_argument("--filter", choices=["api", "database", "manual", "relationship"], 
                        help="Filter by document type")
    
    args = parser.parse_args()
    
    print(f"Searching for: {args.query}")
    print(f"Generating embedding...")
    
    try:
        results = search_docs(args.query, args.limit, args.filter)
        print(f"Found {len(results)} results.")
        print_results(results)
    except Exception as e:
        print(f"Error during search: {str(e)}") 