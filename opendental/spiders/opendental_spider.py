import scrapy
import os

class OpenDentalManualSpider(scrapy.Spider):
    name = 'opendental_manual'
    start_urls = ['https://www.opendental.com/manual243/manual.html']
    custom_settings = {
        'DEPTH_LIMIT': 0,  # Set to 0 to disable depth limit. This *attempts* to scrape all pages.
        'DOWNLOAD_DELAY': 0.25,  # Delay in seconds between requests to be polite. Adjust as needed.
        'ROBOTSTXT_OBEY': True,  # Respect robots.txt rules. Very important.
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',  # Set a user agent
        'FEEDS': {
            'opendental_manual.json': {'format': 'jsonlines'}  # For saving results to a JSON file
        },
        'LOG_LEVEL': 'INFO',  # Set log level for debugging
        'CONCURRENT_REQUESTS': 5,  # Number of concurrent requests
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5  # Limit concurrency per domain
    }

    def __init__(self, output_dir='opendental_manual', *args, **kwargs):
        super(OpenDentalManualSpider, self).__init__(*args, **kwargs)
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def parse(self, response):
        """
        Parses a single page from the Open Dental manual and saves the HTML.
        """
        title = response.xpath('//title/text()').get().strip()

        # Clean the filename
        filename = self.clean_filename(title)
        filepath = os.path.join(self.output_dir, filename)

        # Save the entire response body (HTML) to the file
        with open(filepath, 'wb') as f:  # Use 'wb' for writing bytes
            f.write(response.body)

        self.log(f'Saved page: {title} to {filepath}')

        # Extract all links on the page (relative and absolute)
        for link in response.xpath('//a/@href').getall():
            # Follow the link (Scrapy handles relative/absolute URLs automatically)
            yield response.follow(link, self.parse)  # Recursively call parse for each link

    def clean_filename(self, title):
        """Cleans a title to be a valid and readable filename."""
        import re
        # Remove any characters that are not alphanumeric, spaces, or underscores
        filename = re.sub(r"[^\w\s]", "", title)
        # Replace spaces with underscores
        filename = filename.replace(" ", "_")
        # Limit the filename length to avoid issues with OS limitations
        filename = filename[:100]
        return filename + ".html" 