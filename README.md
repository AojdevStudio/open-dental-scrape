# Open Dental Documentation Search

A simple tool that lets you search and ask questions about Open Dental documentation using natural language.

![Open Dental Logo](https://www.opendental.com/img/ODLogo.png)

## What You Can Do With This Tool

- ✅ Ask questions about Open Dental features in plain English
- ✅ Get accurate answers with links to the official documentation
- ✅ Search across APIs, database schemas, and user manuals in one place
- ✅ Find connections between different parts of Open Dental

## Quick Setup (Recommended)

1. **Install Required Software**
   - Make sure you have [Python 3.10+](https://python.org/downloads) installed
   - Install [Docker Desktop](https://docker.com/products/docker-desktop) and start it

2. **Set Up Your API Key**
   - Create a file named `.env` in the main folder
   - Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`

3. **Run the Setup Script**
   - Open a terminal/command prompt
   - Run this command:
     ```
     bash run_pipeline.sh
     ```
   - You'll see a success message when it's ready

4. **Start the Search Database**
   - In a terminal window, run:
     ```
     docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
     ```
   - Keep this window open while using the search

5. **Search the Documentation**
   - Open a new terminal window
   - Run a search like this:
     ```
     python query_qdrant_fixed.py "How do I create a new patient?"
     ```
   - You'll get relevant answers from the Open Dental documentation

## Troubleshooting

### If the database won't start:
- Make sure Docker Desktop is running
- Check that no other program is using ports 6333 or 6334

### If you get errors during search:
- Verify your OpenAI API key is correct in the `.env` file
- Make sure the database is running in another terminal
- Run `python check_qdrant.py` to check if the database is working

### If results are inaccurate:
- Try rephrasing your question
- Use more specific terms related to Open Dental
- Add `--limit 10` to see more results

## Quick Reference

```
# Start the search database (keep this running)
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant

# Basic search
python query_qdrant_fixed.py "Your question here"

# Get more results
python query_qdrant_fixed.py "Your question here" --limit 10

# Filter by document type
python query_qdrant_fixed.py "Your question here" --filter manual

# Check database status
python check_qdrant.py
```

## Getting Help

If you need assistance:
1. Run `python check_qdrant.py` and note any errors
2. Take a screenshot of your terminal showing the error
3. Contact technical support with the error information
