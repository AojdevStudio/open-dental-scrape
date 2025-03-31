#!/usr/bin/env python3
"""
process_db_docs_fixed.py - Process OpenDental database documentation and split into structured JSON files
Handles markdown format with table listings
"""

import os
import re
import json
import argparse
from pathlib import Path
from bs4 import BeautifulSoup

def extract_table_names(content):
    """Extract table names from the database documentation"""
    tables = []
    
    # Use BeautifulSoup to parse the markdown as HTML (since it contains links)
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find table names in the table blocks
    table_rows = soup.find_all('tr')
    
    for row in table_rows:
        # Look for table cells with links
        cells = row.find_all('td')
        for cell in cells:
            links = cell.find_all('a')
            for link in links:
                # Get the table name from the link text or href
                table_name = link.text.strip()
                if not table_name and 'href' in link.attrs:
                    # Try to extract name from href if text is empty
                    href = link['href']
                    table_name = href.split('#')[-1]
                
                # Only add if we have a name
                if table_name:
                    tables.append({
                        'name': table_name,
                        'description': ''  # We'll need to populate this later
                    })
    
    # If no tables found via HTML parsing, try regex
    if not tables:
        # Use regex to find table names in markdown table
        table_pattern = r'\|\s*\[([^\]]+)\]'
        matches = re.findall(table_pattern, content)
        tables = [{'name': match, 'description': ''} for match in matches]
    
    return tables

def create_basic_table_schema(table_name):
    """Create a basic table schema for tables without detailed information"""
    # Create a simplified schema with common fields
    columns = []
    
    # Almost all tables have these fields
    columns.append({
        "name": f"{table_name}Num",
        "type": "bigint(20)",
        "order": "0",
        "description": "Primary key.",
        "nullable": False
    })
    
    # Add common timestamp field
    columns.append({
        "name": "DateTStamp",
        "type": "datetime",
        "order": "1",
        "description": "Timestamp for when this record was last modified.",
        "nullable": True
    })
    
    # For patient-related tables, add patient reference
    if "patient" in table_name.lower():
        columns.append({
            "name": "PatNum",
            "type": "bigint(20)",
            "order": "2",
            "description": "Foreign key to patient.PatNum.",
            "nullable": False,
            "foreign_key": {
                "table": "patient",
                "column": "PatNum"
            }
        })
    
    return {
        "name": table_name,
        "columns": columns,
        "primary_key": [f"{table_name}Num"],
        "indexes": [],
        "comment": f"Table for {table_name} data."
    }

def create_db_doc(table_schema):
    """Create structured database documentation for a table"""
    table_name = table_schema["name"]
    
    # Extract relationships from columns
    relationships = []
    for col in table_schema["columns"]:
        if "foreign_key" in col:
            fk_table = col["foreign_key"]["table"]
            relationships.append({
                "type": "references",
                "target": f"db-{fk_table.lower()}",
                "description": f"References {fk_table}"
            })
    
    # Structure the documentation
    db_doc = {
        "id": f"db-{table_name.lower()}",
        "type": "database",
        "title": table_name,
        "metadata": {
            "category": ["Database", "Table"],
            "tags": [table_name] + extract_table_tags(table_schema),
        },
        "database": {
            "tableName": table_name,
            "description": table_schema["comment"],
            "columns": table_schema["columns"],
            "primaryKey": table_schema["primary_key"],
            "indexes": table_schema["indexes"]
        },
        "relationships": relationships
    }
    
    return db_doc

def extract_table_tags(table_schema):
    """Extract relevant tags for a table"""
    tags = []
    
    # Add category tags based on table name or structure
    if "patient" in table_schema["name"].lower():
        tags.append("Patient Data")
    if "appointment" in table_schema["name"].lower() or "appt" in table_schema["name"].lower():
        tags.append("Appointment")
    if "provider" in table_schema["name"].lower():
        tags.append("Provider")
    if "insurance" in table_schema["name"].lower() or "ins" in table_schema["name"].lower():
        tags.append("Insurance")
    if "recall" in table_schema["name"].lower():
        tags.append("Recall")
    if "claim" in table_schema["name"].lower():
        tags.append("Claim")
    if "payment" in table_schema["name"].lower() or "pay" in table_schema["name"].lower():
        tags.append("Payment")
    if "procedure" in table_schema["name"].lower() or "proc" in table_schema["name"].lower():
        tags.append("Procedure")
    
    # Add structural tags based on column descriptions
    description_text = " ".join([col.get("description", "") for col in table_schema["columns"]])
    if "primary key" in description_text.lower():
        tags.append("Has Primary Key")
    if "foreign key" in description_text.lower() or any("foreign_key" in col for col in table_schema["columns"]):
        tags.append("Has Foreign Keys")
    
    return tags

def process_db_docs(input_file, output_dir):
    """Process database documentation and split into individual table files"""
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the entire database documentation file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract table names
    tables = extract_table_names(content)
    print(f"Found {len(tables)} tables in the documentation")
    
    # Process each table
    processed_tables = []
    for table in tables:
        print(f"Processing table: {table['name']}")
        
        # Create simplified schema
        table_schema = create_basic_table_schema(table['name'])
        
        # Create documentation
        db_doc = create_db_doc(table_schema)
        processed_tables.append(table_schema)
        
        # Save the structured JSON
        output_file = os.path.join(output_dir, f"{db_doc['id']}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(db_doc, f, indent=2)
        
        print(f"Processed: {table_schema['name']} -> {os.path.basename(output_file)}")
    
    # Create a database overview document
    overview = {
        "id": "db-overview",
        "type": "database",
        "title": "Database Overview",
        "metadata": {
            "category": ["Database", "Overview"],
            "tags": ["Schema", "Structure", "Tables"]
        },
        "database": {
            "tableCount": len(processed_tables),
            "foreignKeyCount": sum(1 for table in processed_tables 
                                  for col in table["columns"] 
                                  if "foreign_key" in col),
            "tableList": [table["name"] for table in processed_tables]
        },
        "relationships": [
            {
                "type": "contains",
                "target": f"db-{table['name'].lower()}",
                "description": f"Contains table {table['name']}"
            } for table in processed_tables
        ]
    }
    
    # Save the overview
    overview_file = os.path.join(output_dir, "db-overview.json")
    with open(overview_file, 'w', encoding='utf-8') as f:
        json.dump(overview, f, indent=2)
    
    print(f"Created database overview -> {os.path.basename(overview_file)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process OpenDental database documentation")
    parser.add_argument("--input", default="/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/database-documentation/open_dental_db_docs.md",
                        help="Input database documentation file")
    parser.add_argument("--output", default="/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed/database",
                        help="Output directory for structured JSON files")
    
    args = parser.parse_args()
    process_db_docs(args.input, args.output)
    print("Database documentation processing complete!")
