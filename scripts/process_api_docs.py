#!/usr/bin/env python3
"""
process_api_docs.py - Convert OpenDental API text files to structured JSON
"""

import os
import re
import json
import argparse
from pathlib import Path

def parse_api_file(file_path):
    """Parse an individual API documentation file and return structured data"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract file name to get the entity name
    file_name = os.path.basename(file_path)
    entity_name = file_name.replace('API ', '').replace('.txt', '')
    
    # Initialize the structure
    api_doc = {
        "id": f"api-{entity_name.lower().replace(' ', '-')}",
        "type": "api",
        "title": entity_name,
        "path": str(file_path),
        "content": content,
        "metadata": {
            "version": extract_version(content),
            "lastUpdated": "",  # Not available in current format
            "category": ["API"],
            "tags": extract_tags(content, entity_name)
        },
        "endpoints": extract_endpoints(content),
        "relationships": extract_relationships(content, entity_name)
    }
    
    return api_doc

def extract_version(content):
    """Extract version information from content"""
    versions = []
    version_pattern = r"Version Added: (\d+\.\d+(?:\.\d+)?)"
    for match in re.finditer(version_pattern, content):
        versions.append(match.group(1))
    
    # Return the newest version if found
    if versions:
        return max(versions, key=lambda v: tuple(map(int, v.split('.'))))
    return ""

def extract_tags(content, entity_name):
    """Extract relevant tags from content"""
    tags = [entity_name]
    
    # Add common operations as tags
    operations = ["GET", "POST", "PUT", "DELETE"]
    for op in operations:
        if f"{entity_name} {op}" in content:
            tags.append(op)
    
    # Look for other potential tags
    if "Required" in content:
        tags.append("Required Fields")
    if "Example" in content:
        tags.append("Examples")
    
    return tags

def extract_endpoints(content):
    """Extract API endpoints information"""
    endpoints = []
    
    # Pattern to match endpoint sections
    endpoint_pattern = r"([A-Za-z]+)\s+(GET|POST|PUT|DELETE)(?:\s+\w+)*\n(Version Added: .+?\n)?(.*?)(?=\n[A-Za-z]+\s+(?:GET|POST|PUT|DELETE)|$)"
    
    for match in re.finditer(endpoint_pattern, content, re.DOTALL):
        resource, method, version_line, endpoint_content = match.groups()
        
        # Extract version if present
        version = ""
        if version_line:
            version_match = re.search(r"Version Added: (\d+\.\d+(?:\.\d+)?)", version_line)
            if version_match:
                version = version_match.group(1)
        
        # Extract parameters
        parameters = []
        param_section = re.search(r"Parameter(?:s)?:(.*?)(?=\n\n|Example|$)", endpoint_content, re.DOTALL)
        if param_section:
            param_text = param_section.group(1).strip()
            param_lines = param_text.split('\n')
            for line in param_lines:
                if ':' in line:
                    name, desc = line.split(':', 1)
                    required = "Required" in desc
                    parameters.append({
                        "name": name.strip(),
                        "description": desc.strip(),
                        "required": required
                    })
        
        # Extract examples
        examples = []
        example_request = re.search(r"Example Request(?:s)?:(.*?)(?=Example Response|$)", endpoint_content, re.DOTALL)
        example_response = re.search(r"Example Response:(.*?)(?=\n\d{3}|$)", endpoint_content, re.DOTALL)
        
        if example_request:
            req = example_request.group(1).strip()
            resp = example_response.group(1).strip() if example_response else ""
            examples.append({
                "request": req,
                "response": resp
            })
        
        # Extract response codes
        responses = []
        response_codes = re.findall(r"(\d{3})\s+([A-Za-z]+)(?:\s+\(([^)]+)\))?", endpoint_content)
        for code, status, desc in response_codes:
            responses.append({
                "code": code,
                "status": status,
                "description": desc
            })
        
        endpoints.append({
            "resource": resource,
            "method": method,
            "path": f"/{resource.lower()}" + ("/List" if "List" in endpoint_content[:100] else ""),
            "versionAdded": version,
            "parameters": parameters,
            "examples": examples,
            "responses": responses,
            "description": extract_description(endpoint_content)
        })
    
    return endpoints

def extract_description(content):
    """Extract the description of an endpoint"""
    # Remove the parameters, examples and response sections
    cleaned = re.sub(r"Parameter(?:s)?:.*?(?=\n\n|Example|$)", "", content, flags=re.DOTALL)
    cleaned = re.sub(r"Example.*?(?=\n\n|\d{3}|$)", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\d{3}\s+[A-Za-z]+(?:\s+\([^)]+\))?", "", cleaned)
    
    # Return the first non-empty paragraph
    paragraphs = [p.strip() for p in cleaned.split('\n\n')]
    for p in paragraphs:
        if p and not p.startswith("Version Added"):
            return p
    
    return ""

def extract_relationships(content, entity_name):
    """Extract relationships to other entities"""
    relationships = []
    
    # Look for "See Also" or "Related" sections
    see_also = re.search(r"See (Also|Related):(.*?)(?=\n\n|$)", content, re.DOTALL)
    if see_also:
        related_text = see_also.group(2).strip()
        for related in re.findall(r"([A-Za-z]+(?:\s+[A-Za-z]+)*)", related_text):
            if related and related != entity_name:
                relationships.append({
                    "type": "related",
                    "target": f"api-{related.lower().replace(' ', '-')}",
                    "description": "Related API"
                })
    
    # Look for references to tables
    table_refs = re.findall(r"(?:table|Table)\s+([a-zA-Z]+)", content)
    for table in set(table_refs):
        relationships.append({
            "type": "references",
            "target": f"db-{table.lower()}",
            "description": f"References database table {table}"
        })
    
    return relationships

def process_api_docs(input_dir, output_dir):
    """Process all API documentation files in a directory"""
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all API text files
    api_files = list(Path(input_dir).glob("API *.txt"))
    print(f"Found {len(api_files)} API documentation files")
    
    # Process each file
    for file_path in api_files:
        try:
            api_doc = parse_api_file(file_path)
            
            # Save the structured JSON
            output_file = os.path.join(output_dir, f"{api_doc['id']}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(api_doc, f, indent=2)
                
            print(f"Processed: {file_path.name} -> {os.path.basename(output_file)}")
        except Exception as e:
            print(f"Error processing {file_path.name}: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process OpenDental API documentation")
    parser.add_argument("--input", default="/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/api-documentation",
                        help="Input directory containing API text files")
    parser.add_argument("--output", default="/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed/api",
                        help="Output directory for structured JSON files")
    
    args = parser.parse_args()
    process_api_docs(args.input, args.output)
    print("API documentation processing complete!")
