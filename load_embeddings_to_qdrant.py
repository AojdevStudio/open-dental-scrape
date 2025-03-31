from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import json
from pathlib import Path
from tqdm import tqdm  # For progress bar

# Connect to your local Qdrant instance
client = QdrantClient(host="localhost", port=6333)

# Define the collection parameters
vector_size = 1536  # Assuming OpenAI embeddings dimension
collection_name = "open_dental_docs"

# Check if collection exists and create it if it doesn't
collections = client.get_collections().collections
collection_names = [collection.name for collection in collections]

if collection_name not in collection_names:
    print(f"Creating collection '{collection_name}'...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
else:
    print(f"Collection '{collection_name}' already exists")

# Load your existing embeddings
embeddings_dir = Path("./local_embeddings")
combined_file = embeddings_dir / "combined_embeddings.json"

with open(combined_file, "r") as f:
    print("Loading embeddings from file...")
    data = json.load(f)
    chunks = data["chunks"]
    print(f"Loaded {len(chunks)} chunks")

# Prepare points for upload
points = []
for chunk in chunks:
    # Convert string IDs to integers if needed
    # Qdrant supports both string and integer IDs
    try:
        point_id = int(chunk["id"])
    except (ValueError, TypeError):
        point_id = chunk["id"]  # Keep as string if not convertible
    
    point = PointStruct(
        id=point_id,
        vector=chunk["embedding"],
        payload={
            "text": chunk["text"],
            "title": chunk["metadata"].get("title", ""),
            "type": chunk["metadata"].get("type", ""),
            "category": chunk["metadata"].get("category", ""),
            # Add other metadata fields as needed
        }
    )
    points.append(point)

# Upload in batches
batch_size = 100
total_batches = (len(points) + batch_size - 1) // batch_size

print(f"Uploading {len(points)} points in {total_batches} batches...")
for i in tqdm(range(0, len(points), batch_size)):
    batch = points[i:i + batch_size]
    client.upsert(
        collection_name=collection_name,
        points=batch
    )

print("Upload complete!")

# Print some collection stats to verify
collection_info = client.get_collection(collection_name=collection_name)
print(f"Collection '{collection_name}' now has {collection_info.vectors_count} vectors")