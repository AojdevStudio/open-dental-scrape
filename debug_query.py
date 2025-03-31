from qdrant_client import QdrantClient
from openai import OpenAI
import os
import dotenv
import json
import sys

# Load environment variables from .env file
print("Loading environment variables...")
dotenv.load_dotenv()

# Verify OpenAI API key
openai_key = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key loaded: {openai_key is not None}")
if not openai_key:
    print("ERROR: OpenAI API key not found in environment variables!")
    sys.exit(1)

# Set up OpenAI client
print("Setting up OpenAI client...")
try:
    client_openai = OpenAI(api_key=openai_key)
    print("OpenAI client initialized successfully.")
except Exception as e:
    print(f"ERROR initializing OpenAI client: {str(e)}")
    sys.exit(1)

# Connect to Qdrant
print("Connecting to Qdrant...")
qdrant_url = os.getenv("QDRANT_HOST")
qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
print(f"Using Qdrant URL: {qdrant_url}, port: {qdrant_port}")

try:
    # Check if URL contains protocol
    if qdrant_url and (qdrant_url.startswith("http://") or qdrant_url.startswith("https://")):
        print("Using URL parameter for Qdrant client")
        qdrant_client = QdrantClient(url=qdrant_url)
    else:
        print("Using host parameter for Qdrant client")
        qdrant_client = QdrantClient(host="localhost", port=qdrant_port)
    
    print("Qdrant client initialized successfully.")
except Exception as e:
    print(f"ERROR connecting to Qdrant: {str(e)}")
    sys.exit(1)

collection_name = "open_dental_docs"

# Check collection exists
print(f"Checking if collection '{collection_name}' exists...")
try:
    collection_info = qdrant_client.get_collection(collection_name=collection_name)
    print(f"Collection info: {collection_info}")
except Exception as e:
    print(f"ERROR getting collection info: {str(e)}")
    sys.exit(1)

# Test query
query_text = "How to create a patient in Open Dental?"
print(f"Testing query: '{query_text}'")

# Get embedding
print("Generating embedding...")
try:
    response = client_openai.embeddings.create(
        input=query_text,
        model="text-embedding-ada-002"
    )
    query_vector = response.data[0].embedding
    print(f"Generated embedding with {len(query_vector)} dimensions")
except Exception as e:
    print(f"ERROR generating embedding: {str(e)}")
    sys.exit(1)

# Search in Qdrant
print("Searching in Qdrant...")
try:
    search_result = qdrant_client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=5
    )
    print(f"Search returned {len(search_result)} results.")
    
    if len(search_result) > 0:
        print("\n=== SEARCH RESULTS ===\n")
        for i, result in enumerate(search_result):
            print(f"Result {i+1} (Score: {result.score:.4f}):")
            print(f"ID: {result.id}")
            print(f"Original ID: {result.payload.get('original_id', 'Unknown')}")
            print(f"Type: {result.payload.get('type', 'Unknown')}")
            print(f"Title: {result.payload.get('title', 'Untitled')}")
            print(f"Text snippet: {result.payload.get('text', '')[:150]}...")
            print("-" * 80)
    else:
        print("No results found!")
except Exception as e:
    print(f"ERROR during search: {str(e)}")
    sys.exit(1)

print("\nDebug complete!") 