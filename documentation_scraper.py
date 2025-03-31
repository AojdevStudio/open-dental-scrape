import requests
from bs4 import BeautifulSoup
import json
import logging
from urllib.parse import urlparse
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_filename(url):
    """Generates a filename based on the URL's domain and path."""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('.', '_').replace('-', '_')
        path = parsed_url.path.strip('/').replace('/', '_').replace('.', '_')
        if not path:
            path = 'index'
        # Limit filename length
        max_len = 100
        filename = f"{domain}_{path}"
        return filename[:max_len] + ".txt"
    except Exception as e:
        logger.warning(f"Could not generate filename from URL {url}: {e}")
        return "scraped_content.txt"

if __name__ == "__main__":
    target_url = input("Enter the URL you'd like to scrape: ").strip()

    if not target_url:
        print("No URL entered. Exiting.")
    else:
        logger.info(f"Attempting to extract raw text from: {target_url}")

        # 1. Fetch the content
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(target_url, headers=headers, timeout=20)
            response.raise_for_status() # Check for HTTP errors
            html_content = response.text
            logger.info(f"Successfully fetched content from {target_url}")

        except requests.exceptions.Timeout:
            logger.error(f"Request timed out while fetching {target_url}")
            exit()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch URL {target_url}: {e}")
            exit()
        except Exception as e:
             logger.error(f"An unexpected error occurred during fetching: {e}")
             exit()

        # 2. Extract raw text using BeautifulSoup
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Get all text from the body, separated by space, stripping extra whitespace
            raw_text = ""
            if soup.body:
                 raw_text = soup.body.get_text(separator=' ', strip=True)
            else:
                 # Fallback if no body tag is found (unlikely for HTML)
                 raw_text = soup.get_text(separator=' ', strip=True)

            if raw_text:
                logger.info("Successfully extracted raw text using BeautifulSoup.")
                output_filename = generate_filename(target_url)
                logger.info(f"Saving extracted text to: {output_filename}")

                try:
                    with open(output_filename, 'w', encoding='utf-8') as f:
                        f.write(raw_text)
                    logger.info("Content saved successfully.")
                except IOError as e:
                     logger.error(f"Failed to write output file {output_filename}: {e}")
                except Exception as e:
                     logger.error(f"An unexpected error occurred during saving: {e}")

            else:
                logger.warning(f"BeautifulSoup could not extract any text content from {target_url}.")

        except Exception as e:
            logger.error(f"An error occurred during text extraction with BeautifulSoup: {e}") 