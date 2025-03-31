from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
collection_name = "open_dental_docs"

try:
    # Get collection info
    collection_info = client.get_collection(collection_name=collection_name)
    print(f"Collection info: {collection_info}")
    
    # Count points
    count_result = client.count(collection_name=collection_name)
    print(f"Point count: {count_result.count}")
    
    # Get a few points to check
    points = client.scroll(
        collection_name=collection_name,
        limit=5,
        with_payload=True,
        with_vectors=False
    )
    print(f"First 5 points:")
    for point in points[0]:
        print(f"  ID: {point.id}")
        print(f"  Payload: {point.payload}")
        print("---")
    
except Exception as e:
    print(f"Error: {str(e)}") 