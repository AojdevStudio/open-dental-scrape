# Open Dental Documentation Search

This easy-to-follow guide will help you set up and use the Open Dental Documentation Search system, which lets you ask questions about Open Dental and get accurate answers from the documentation.

![Open Dental Logo](https://www.opendental.com/img/ODLogo.png)

## What This Tool Does

This tool allows you to:
- Search through Open Dental documentation using natural language questions
- Get precise answers with references to the original documentation
- Find information across APIs, database schemas, and manuals

## Step-by-Step Setup Guide

### Option 1: Quick Setup (Recommended for Most Users)

For the easiest setup experience, you can use our automated pipeline script:

1. Make sure you have Python and Docker installed (see Step 1 in the Detailed Setup below)
2. Create a `.env` file with your OpenAI API key (see Step 2.3 in the Detailed Setup below)
3. Open a terminal and run:

```
bash run_pipeline.sh
```

This single command will:
- Prepare the code embeddings
- Generate local embeddings
- Tell you when it's ready to use

After running this script, you can skip to Step 3 (Start the Search Database) in the Detailed Setup.

### Option 2: Detailed Setup

#### Step 1: Install Required Software

#### Install Python

If you don't already have Python installed:

1. Go to [python.org/downloads](https://python.org/downloads)
2. Download and install Python 3.10 or newer
3. Make sure to check "Add Python to PATH" during installation

#### Install Docker

Docker is needed to run the search database:

1. Go to [docker.com/products/docker-desktop](https://docker.com/products/docker-desktop)
2. Download and install Docker Desktop
3. Start Docker Desktop after installation

### Step 2: Set Up the Project

1. Open a terminal or command prompt
   - **Windows**: Search for "Command Prompt" or "PowerShell"
   - **Mac**: Search for "Terminal" in Spotlight
   - **Linux**: Use your terminal application

2. Install the required Python packages by copying and pasting this command:

```
pip install qdrant-client openai python-dotenv tqdm
```

3. Create a file named `.env` in the project folder with your OpenAI API key:
   - Open a text editor (like Notepad, TextEdit, or VS Code)
   - Copy and paste the following, replacing `your_api_key_here` with your actual OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

   - Save the file as `.env` in the project folder

### Step 3: Start the Search Database

1. Start the Qdrant database by copying and pasting this command into your terminal:

```
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

2. Keep this terminal window open! The database will run in this window.

### Step 4: Load Documentation into the Search Database

1. Open a new terminal or command prompt window
2. Navigate to the project folder
3. Run the loading script by copying and pasting this command:

```
python load_embeddings_to_qdrant_fixed.py
```

4. Wait for the loading to complete - you'll see a message saying "Upload complete!"

### Step 5: Search the Documentation

Now you can start searching! Use this command format:

```
python query_qdrant_fixed.py "Your question about Open Dental goes here?"
```

For example:

```
python query_qdrant_fixed.py "How do I create a new patient record?"
```

#### Advanced Search Options:

- To get more results, add `--limit` followed by a number:
  ```
  python query_qdrant_fixed.py "How do I create a new patient record?" --limit 10
  ```

- To search only specific document types, add `--filter` followed by one of: api, database, manual, relationship:
  ```
  python query_qdrant_fixed.py "How do I create a new patient record?" --filter manual
  ```

## Troubleshooting

If you encounter any issues:

### The database won't start
- Make sure Docker Desktop is running
- Try restarting Docker Desktop
- Make sure no other program is using ports 6333 or 6334

### Loading errors
- Check that your `.env` file exists and contains your OpenAI API key
- Make sure the local_embeddings folder contains the combined_embeddings.json file
- Try running `python check_qdrant.py` to verify the database is working

### Search isn't working
- Make sure the database is still running in the first terminal window
- Verify that embeddings were loaded successfully
- Check your internet connection (needed for OpenAI embeddings)

## Need More Help?

If you're still having trouble, please contact technical support with:
1. A screenshot of any error messages
2. The steps you followed
3. What you expected to happen

## Quick Reference Commands

Here's a summary of all the commands you'll need:

```
# OPTION 1: Run the entire pipeline (easiest)
bash run_pipeline.sh

# OPTION 2: Manual steps
# Install packages
pip install qdrant-client openai python-dotenv tqdm

# Start database (keep this running in a terminal)
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant

# Load documentation (in a new terminal)
python load_embeddings_to_qdrant_fixed.py

# Search the documentation
python query_qdrant_fixed.py "Your question here?"

# Check if database is working properly
python check_qdrant.py
```

## Structure of embeddings file

The expected format for `combined_embeddings.json` is:

```json
{
  "chunks": [
    {
      "id": "some-id",
      "text": "Document text content",
      "embedding": [0.1, 0.2, ...],
      "metadata": {
        "title": "Document title",
        "type": "Document type",
        "category": "Optional category"
      }
    },
    ...
  ]
}
```
