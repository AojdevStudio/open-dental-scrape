import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Check OpenAI API key
openai_key = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key loaded: {openai_key is not None}")
if openai_key:
    print(f"Key starts with: {openai_key[:10]}...")

# Check Qdrant settings
qdrant_host = os.getenv("QDRANT_HOST")
qdrant_port = os.getenv("QDRANT_PORT")
print(f"Qdrant Host: {qdrant_host}")
print(f"Qdrant Port: {qdrant_port}") 