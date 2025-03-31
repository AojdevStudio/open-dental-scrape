from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import json
from pathlib import Path
from tqdm import tqdm
import uuid

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
id_mapping = {}  # Store mapping between original IDs and new UUIDs

for chunk in chunks:
    # Create a UUID for each point
    point_id = str(uuid.uuid4())
    
    # Store the mapping
    id_mapping[chunk["id"]] = point_id
    
    points.append({
        "id": point_id,
        "vector": chunk["embedding"],
        "payload": {
            "original_id": chunk["id"],  # Keep the original ID in payload
            "text": chunk["text"],
            "title": chunk["metadata"].get("title", ""),
            "type": chunk["metadata"].get("type", ""),
            "category": chunk["metadata"].get("category", "")
        }
    })

# Save the ID mapping for future reference
with open("id_mapping.json", "w") as f:
    json.dump(id_mapping, f)
    print(f"Saved ID mapping to id_mapping.json")

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