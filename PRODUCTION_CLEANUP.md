# Production Deployment Recommendations

This document provides guidance on which files are necessary for production and which can be removed.

## Files to Keep

### Core Scripts
- `run_pipeline.sh` - Main pipeline script for data processing
- `load_embeddings_to_qdrant_fixed.py` - Script to load embeddings into Qdrant (production version)
- `query_qdrant_fixed.py` - Script to query Qdrant (production version)
- `check_qdrant.py` - Utility to verify Qdrant database status

### Processing Scripts
- `scripts/prepare_code_embeddings.py` - Prepares embeddings from documentation
- `scripts/prepare_local_embeddings.py` - Generates OpenAI embeddings

### Configuration
- `requirements.txt` - Dependencies list
- `.env` - Configuration file (but replace API keys with placeholders)
- `.gitignore` - Version control exclusion rules

### Documentation
- `README.md` - User documentation

### Data
- `local_embeddings/` - Generated embeddings
- `qdrant_storage/` - Database storage
- `embeddings/` - Processed embeddings

### Docker
- `docker/` - Docker configuration (if needed for deployment)

## Files to Remove

### Redundant Scripts
- `load_embeddings_to_qdrant.py` - Replaced by fixed version
- `query_qdrant.py` - Replaced by fixed version

### Development Tools
- `debug_query.py` - Development debugging tool
- `watcher.py` - Development utility
- `test_env.py` - Testing utility

### Data Collection Scripts (Not Needed Post-Scraping)
- `documentation_scraper.py` - One-time scraping utility
- `parse_xml_schema.py` - One-time parsing utility
- `scraper.py` - One-time scraping utility
- `spiders/` - Scrapy spiders for scraping

### Environment and System Files
- `settings.py` - Obsolete if settings are in .env
- `.venv/`, `venv/`, `env/` - Virtual environments
- `.DS_Store` - macOS system file
- `.cursor/` - Editor configuration
- `.cursorrules` - Editor configuration

### Development Documentation
- `TASK_LOG.md` - Development log

## Recommendations

1. **Clean API Keys**: Ensure no actual API keys are included in the production deployment.

2. **Simplify Directory Structure**: Consider reorganizing the directory structure to be more intuitive:
   ```
   open-dental-search/
   ├── scripts/            # Processing scripts
   ├── data/               # Data storage (embeddings, Qdrant)
   └── docs/               # Documentation
   ```

3. **Docker Deployment**: Consider containerizing the entire application for easier deployment.

4. **Requirements Cleanup**: Review requirements.txt to ensure it only includes necessary dependencies.

5. **Error Handling**: Enhance error handling in production scripts to be more user-friendly.

6. **User Documentation**: Continue to refine the README for clarity and ease of use.

7. **Security**: Ensure proper handling of API keys and sensitive data. 