#!/usr/bin/env python3
"""
process_db_docs.py - Process OpenDental database documentation and split into structured JSON files
"""

import os
import re
import json
import argparse
from pathlib import Path

def extract_table_schema(content):
    """Extract all table definitions from the database documentation"""
    tables = []
    
    # Pattern to match CREATE TABLE statements
    table_pattern = r"CREATE TABLE `([^`]+)`\s*\(\s*(.*?)\s*\)\s*ENGINE=(?:InnoDB|MyISAM)(.*?(?=CREATE TABLE|$))"
    
    for match in re.finditer(table_pattern, content, re.DOTALL):
        table_name, columns_text, extra = match.groups()
        
        # Process columns
        columns = []
        column_pattern = r"`([^`]+)`\s+([^,]+)(?:,|$)"
        for col_match in re.finditer(column_pattern, columns_text, re.DOTALL):
            col_name, col_type_def = col_match.groups()
            
            # Extract data type
            type_match = re.search(r"([A-Za-z]+)(?:\(([^)]+)\))?", col_type_def)
            if type_match:
                col_type = type_match.group(1)
                col_size = type_match.group(2) if type_match.group(2) else ""
            else:
                col_type = col_type_def.strip()
                col_size = ""
            
            # Check for NULL/NOT NULL
            nullable = "NOT NULL" not in col_type_def
            
            # Check for default value
            default_match = re.search(r"DEFAULT\s+('(?:[^'\\]|\\.)*'|\d+|NULL)", col_type_def)
            default_value = default_match.group(1) if default_match else None
            
            # Check for auto_increment
            auto_increment = "AUTO_INCREMENT" in col_type_def
            
            columns.append({
                "name": col_name,
                "type": col_type,
                "size": col_size,
                "nullable": nullable,
                "default": default_value,
                "auto_increment": auto_increment,
                "description": extract_column_comment(table_name, col_name, extra)
            })
        
        # Extract primary key
        primary_key = []
        pk_match = re.search(r"PRIMARY KEY\s*\(([^)]+)\)", columns_text)
        if pk_match:
            primary_key = [key.strip('` ') for key in pk_match.group(1).split(',')]
        
        # Extract indexes
        indexes = []
        index_pattern = r"(UNIQUE\s+)?KEY\s+`([^`]+)`\s*\(([^)]+)\)"
        for idx_match in re.finditer(index_pattern, columns_text):
            unique, idx_name, idx_columns = idx_match.groups()
            indexes.append({
                "name": idx_name,
                "columns": [col.strip('` ') for col in idx_columns.split(',')],
                "unique": bool(unique)
            })
        
        # Extract table comment if available
        comment_match = re.search(r"COMMENT\s*=\s*'((?:[^'\\]|\\.)*)'", extra)
        table_comment = comment_match.group(1) if comment_match else ""
        
        tables.append({
            "name": table_name,
            "columns": columns,
            "primary_key": primary_key,
            "indexes": indexes,
            "comment": table_comment
        })
    
    return tables

def extract_column_comment(table_name, column_name, content):
    """Extract column comment if available"""
    comment_pattern = r"COLUMN_COMMENT\s*=\s*'((?:[^'\\]|\\.)*)'.*?`" + re.escape(table_name) + r"`.*?`" + re.escape(column_name) + r"`"
    comment_match = re.search(comment_pattern, content, re.DOTALL)
    return comment_match.group(1) if comment_match else ""

def extract_foreign_keys(content):
    """Extract foreign key relationships"""
    foreign_keys = []
    
    # Pattern to match ALTER TABLE ADD CONSTRAINT statements for foreign keys
    fk_pattern = r"ALTER TABLE `([^`]+)`\s+ADD CONSTRAINT.*?FOREIGN KEY\s*\(`([^`]+)`\)\s*REFERENCES\s*`([^`]+)`\s*\(`([^`]+)`\)"
    
    for match in re.finditer(fk_pattern, content, re.DOTALL):
        table_name, column_name, ref_table, ref_column = match.groups()
        
        foreign_keys.append({
            "table": table_name,
            "column": column_name,
            "references_table": ref_table,
            "references_column": ref_column
        })
    
    return foreign_keys

def create_db_doc(table_schema, foreign_keys):
    """Create structured database documentation for a table"""
    table_name = table_schema["name"]
    
    # Find foreign keys for this table
    table_fks = []
    for fk in foreign_keys:
        if fk["table"] == table_name:
            # Add foreign key info to the corresponding column
            for i, col in enumerate(table_schema["columns"]):
                if col["name"] == fk["column"]:
                    table_schema["columns"][i]["foreign_key"] = {
                        "table": fk["references_table"],
                        "column": fk["references_column"]
                    }
            
            table_fks.append(fk)
    
    # Find relationships from other tables to this one
    relationships = []
    for fk in foreign_keys:
        if fk["references_table"] == table_name:
            relationships.append({
                "type": "referenced_by",
                "target": f"db-{fk['table'].lower()}",
                "description": f"Referenced by {fk['table']}.{fk['column']}"
            })
    
    # Add relationships to tables this table references
    for fk in table_fks:
        relationships.append({
            "type": "references",
            "target": f"db-{fk['references_table'].lower()}",
            "description": f"References {fk['references_table']}.{fk['references_column']}"
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
    if "appointment" in table_schema["name"].lower():
        tags.append("Appointment")
    if "provider" in table_schema["name"].lower():
        tags.append("Provider")
    if "insurance" in table_schema["name"].lower() or "ins" in table_schema["name"].lower():
        tags.append("Insurance")
    if "recall" in table_schema["name"].lower():
        tags.append("Recall")
    
    # Add structural tags
    if any(col.get("auto_increment", False) for col in table_schema["columns"]):
        tags.append("Auto Increment")
    if table_schema["indexes"]:
        tags.append("Indexed")
    
    return tags

def process_db_docs(input_file, output_dir):
    """Process database documentation and split into individual table files"""
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the entire database documentation file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract table schemas and foreign keys
    table_schemas = extract_table_schema(content)
    foreign_keys = extract_foreign_keys(content)
    
    print(f"Found {len(table_schemas)} tables and {len(foreign_keys)} foreign key relationships")
    
    # Process each table
    for table_schema in table_schemas:
        db_doc = create_db_doc(table_schema, foreign_keys)
        
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
            "tableCount": len(table_schemas),
            "foreignKeyCount": len(foreign_keys),
            "tableList": [table["name"] for table in table_schemas]
        },
        "relationships": [
            {
                "type": "contains",
                "target": f"db-{table['name'].lower()}",
                "description": f"Contains table {table['name']}"
            } for table in table_schemas
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
