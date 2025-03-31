import requests
from bs4 import BeautifulSoup
import json
import logging
from urllib.parse import urljoin, urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_website(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('.', '_')
    if not domain:
        domain = "unknown_site"
    output_filename = f"{domain}_content.json"
    logger.info(f"Starting scrape for {url}. Output will be saved to {output_filename}")

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch initial URL {url}: {e}")
        return

    soup = BeautifulSoup(response.text, 'lxml')
    
    toc = {}
    left_tree = soup.find('ul', class_='LeftTreeFirstNode')
    if left_tree:
        for item in left_tree.find_all('li', recursive=True):
            link = item.find('a')
            if link:
                title = link.text.strip()
                href = link.get('href', '')
                absolute_href = urljoin(url, href)
                toc[title] = absolute_href
    else:
        logger.warning("Could not find Table of Contents using selector 'ul.LeftTreeFirstNode'. The target site might have a different structure.")

    manual_content = {}
    total_pages = len(toc)
    logger.info(f"Found {total_pages} pages to process from the TOC.")
    
    if total_pages == 0:
        logger.info("No pages found in TOC. Scraping main page content only (if possible).")
        content_div = soup.find('div', class_='RightMain')
        if content_div:
            logger.info(f"Attempting to extract content directly from {url}")
            content = extract_content_from_div(content_div)
            manual_content["main_page"] = content
        else:
            logger.warning(f"Could not find content using selector 'div.RightMain' on the main page {url}.")

    for i, (title, href) in enumerate(toc.items(), 1):
        try:
            logger.info(f"Processing page {i}/{total_pages}: {title} ({href})")
            page_response = requests.get(href)
            page_response.raise_for_status()
            page_soup = BeautifulSoup(page_response.text, 'lxml')
            
            content_div = page_soup.find('div', class_='RightMain')
            if content_div:
                content = extract_content_from_div(content_div)
                manual_content[title] = content
            else:
                 logger.warning(f"Could not find content using selector 'div.RightMain' on page: {title} ({href})")
                
            if i % 10 == 0:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(manual_content, f, indent=2, ensure_ascii=False)
                logger.info(f"Progress saved: {i}/{total_pages} pages processed")
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {title} ({href}): {e}")
        except Exception as e:
            logger.error(f"Error processing page {title} ({href}): {e}")
    
    if manual_content:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(manual_content, f, indent=2, ensure_ascii=False)
        logger.info(f"Complete! {len(manual_content)} sections processed and saved to {output_filename}")
    else:
        logger.info("No content was successfully scraped.")

def extract_content_from_div(content_div):
    content = []
    for elem in content_div.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol'], recursive=False):
        if elem.name in ['h1', 'h2', 'h3', 'h4']:
            content.append({'type': 'header', 'level': int(elem.name[1]), 'text': elem.text.strip()})
        elif elem.name == 'p':
            content.append({'type': 'paragraph', 'text': elem.text.strip()})
        elif elem.name in ['ul', 'ol']:
            items = [li.text.strip() for li in elem.find_all('li')]
            list_type = 'unordered' if elem.name == 'ul' else 'ordered'
            content.append({'type': 'list', 'list_type': list_type, 'items': items})
    return content

if __name__ == "__main__":
    # Get URL via interactive input
    target_url = input("Enter the URL you'd like to scrape: ")
    if target_url:
        # Call the scraping function with the provided URL
        scrape_website(target_url.strip())
    else:
        print("No URL entered. Exiting.")

# if __name__ == "__main__":
#     scrape_open_dental_manual() 