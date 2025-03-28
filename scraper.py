import requests
from bs4 import BeautifulSoup
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_open_dental_manual():
    url = "https://www.opendental.com/manual243/manual.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    
    # Get the table of contents
    toc = {}
    left_tree = soup.find('ul', class_='LeftTreeFirstNode')
    if left_tree:
        for item in left_tree.find_all('li', recursive=True):
            link = item.find('a')
            if link:
                title = link.text.strip()
                href = link.get('href', '')
                if href.startswith('..'):
                    href = 'https://www.opendental.com' + href[2:]
                toc[title] = href
    
    # Get content for each page
    manual_content = {}
    total_pages = len(toc)
    logger.info(f"Found {total_pages} pages to process")
    
    for i, (title, href) in enumerate(toc.items(), 1):
        try:
            logger.info(f"Processing page {i}/{total_pages}: {title}")
            page = requests.get(href)
            page_soup = BeautifulSoup(page.text, 'lxml')
            
            # Get main content
            content_div = page_soup.find('div', class_='RightMain')
            if content_div:
                content = []
                for elem in content_div.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol']):
                    if elem.name in ['h1', 'h2', 'h3', 'h4']:
                        content.append({'type': 'header', 'level': int(elem.name[1]), 'text': elem.text.strip()})
                    elif elem.name == 'p':
                        content.append({'type': 'paragraph', 'text': elem.text.strip()})
                    elif elem.name in ['ul', 'ol']:
                        items = [li.text.strip() for li in elem.find_all('li')]
                        content.append({'type': 'list', 'items': items})
                manual_content[title] = content
                
                # Save progress every 10 pages
                if i % 10 == 0:
                    with open('manual_content.json', 'w', encoding='utf-8') as f:
                        json.dump(manual_content, f, indent=2, ensure_ascii=False)
                    logger.info(f"Progress saved: {i}/{total_pages} pages processed")
                    
        except Exception as e:
            logger.error(f"Error fetching {title}: {e}")
    
    # Final save
    with open('manual_content.json', 'w', encoding='utf-8') as f:
        json.dump(manual_content, f, indent=2, ensure_ascii=False)
        logger.info(f"Complete! All {total_pages} pages processed and saved to manual_content.json")

if __name__ == "__main__":
    scrape_open_dental_manual() 