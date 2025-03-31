import requests
import json
import logging
from lxml import etree # Using lxml for robust XML parsing
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_schema(xml_content):
    """Parses the XML database schema content."""
    schema_data = {}
    database_version = "unknown"
    try:
        # Parse the XML. Need to encode to bytes for lxml.etree.fromstring
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(xml_content.encode('utf-8'), parser=parser)

        if root.tag != 'database':
            logger.error("Root element is not '<database>'. Is this the correct XML schema file?")
            return None, database_version

        database_version = root.get('version', 'unknown')
        schema_data['database_version'] = database_version
        schema_data['tables'] = {}

        logger.info(f"Parsing database schema version: {database_version}")

        for table_elem in root.xpath('./table'):
            table_name = table_elem.get('name')
            if not table_name:
                logger.warning("Found a table element without a name attribute. Skipping.")
                continue

            logger.debug(f"Processing table: {table_name}")
            table_summary = table_elem.xpath('./summary/text()')
            table_info = {
                'summary': table_summary[0].strip() if table_summary else '',
                'columns': []
            }

            for col_elem in table_elem.xpath('./column'):
                col_info = {
                    'order': col_elem.get('order'),
                    'name': col_elem.get('name'),
                    'type': col_elem.get('type'),
                    'fk': col_elem.get('fk'), # Will be None if attribute doesn't exist
                    'summary': '',
                    'enumeration': None
                }

                col_summary = col_elem.xpath('./summary/text()')
                if col_summary:
                    col_info['summary'] = col_summary[0].strip()

                enum_elem = col_elem.xpath('./Enumeration')
                if enum_elem:
                    enum_info = {
                        'name': enum_elem[0].get('name'),
                        'summary': '',
                        'values': {}
                    }
                    enum_summary = enum_elem[0].xpath('./summary/text()')
                    if enum_summary:
                        enum_info['summary'] = enum_summary[0].strip()

                    for enum_val_elem in enum_elem[0].xpath('./EnumValue'):
                        val_name = enum_val_elem.get('name')
                        val_value = enum_val_elem.text
                        if val_name is not None:
                            enum_info['values'][val_name] = val_value.strip() if val_value else None
                    col_info['enumeration'] = enum_info

                # Remove fk if it's None for cleaner output
                if col_info['fk'] is None:
                    del col_info['fk']

                table_info['columns'].append(col_info)

            schema_data['tables'][table_name] = table_info

        return schema_data, database_version

    except etree.XMLSyntaxError as e:
        logger.error(f"Error parsing XML: {e}")
        return None, database_version
    except Exception as e:
        logger.error(f"An unexpected error occurred during parsing: {e}")
        return None, database_version


if __name__ == "__main__":
    target_url = input("Enter the XML Schema URL you'd like to parse: ").strip()

    if not target_url:
        print("No URL entered. Exiting.")
    else:
        logger.info(f"Fetching XML schema from: {target_url}")
        try:
            response = requests.get(target_url, timeout=30) # Added timeout
            response.raise_for_status() # Check for HTTP errors (4xx or 5xx)

            # Check content type (optional but good practice)
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' not in content_type:
                logger.warning(f"Content-Type is '{content_type}', not XML. Parsing might fail.")

            xml_content = response.text
            logger.info("Successfully fetched XML content.")

            parsed_data, db_version = parse_schema(xml_content)

            if parsed_data:
                # Create filename based on version or domain
                if db_version != "unknown":
                     output_filename = f"database_schema_v{db_version}.json"
                else:
                    try:
                        domain = urlparse(target_url).netloc.replace('.', '_')
                        output_filename = f"{domain}_schema.json" if domain else "unknown_schema.json"
                    except Exception:
                        output_filename = "unknown_schema.json"

                logger.info(f"Saving parsed schema to: {output_filename}")
                try:
                    with open(output_filename, 'w', encoding='utf-8') as f:
                        json.dump(parsed_data, f, indent=2, ensure_ascii=False)
                    logger.info("Schema saved successfully.")
                except IOError as e:
                    logger.error(f"Failed to write output file {output_filename}: {e}")
            else:
                logger.error("Failed to parse XML schema.")

        except requests.exceptions.Timeout:
            logger.error(f"Request timed out while fetching {target_url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch URL {target_url}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}") 