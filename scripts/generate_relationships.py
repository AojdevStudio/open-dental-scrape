#!/usr/bin/env python3
"""
generate_relationships.py - Generate cross-document relationships between API, Database, and Manual documentation
"""

import os
import json
import argparse
import re
from pathlib import Path

def load_processed_docs(base_dir):
    """Load all processed documentation files"""
    api_docs = load_docs_from_dir(os.path.join(base_dir, "api"))
    db_docs = load_docs_from_dir(os.path.join(base_dir, "database"))
    manual_docs = load_docs_from_dir(os.path.join(base_dir, "manual"))
    
    return {
        "api": api_docs,
        "database": db_docs,
        "manual": manual_docs
    }

def load_docs_from_dir(directory):
    """Load all JSON files from a directory"""
    docs = {}
    if not os.path.exists(directory):
        return docs
    
    for file_path in Path(directory).glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                doc = json.load(f)
                doc_id = doc.get("id", os.path.basename(file_path).replace(".json", ""))
                docs[doc_id] = doc
        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
    
    return docs

def find_api_db_relationships(api_docs, db_docs):
    """Find relationships between API docs and database docs"""
    relationships = []
    
    # For each API doc, look for references to database tables
    for api_id, api_doc in api_docs.items():
        api_content = json.dumps(api_doc).lower()
        
        # Check for each database table
        for db_id, db_doc in db_docs.items():
            if db_id == "db-overview":
                continue
                
            table_name = db_doc.get("database", {}).get("tableName", "").lower()
            if not table_name:
                continue
                
            # Check if API doc mentions this table
            if table_name in api_content:
                # Create relationship in both directions
                relationships.append({
                    "source_id": api_id,
                    "target_id": db_id,
                    "type": "references",
                    "description": f"API references database table {table_name}"
                })
                
                relationships.append({
                    "source_id": db_id,
                    "target_id": api_id,
                    "type": "referenced_by",
                    "description": f"Database table referenced by API"
                })
    
    return relationships

def find_api_manual_relationships(api_docs, manual_docs):
    """Find relationships between API docs and manual docs"""
    relationships = []
    
    # For each API doc, look for references in manual docs
    for api_id, api_doc in api_docs.items():
        api_title = api_doc.get("title", "").lower()
        if not api_title:
            continue
            
        # Check each manual doc for references to this API
        for manual_id, manual_doc in manual_docs.items():
            manual_content = json.dumps(manual_doc.get("manual", {}).get("content", [])).lower()
            
            if api_title in manual_content:
                # Create relationship in both directions
                relationships.append({
                    "source_id": manual_id,
                    "target_id": api_id,
                    "type": "references",
                    "description": f"Manual section references API"
                })
                
                relationships.append({
                    "source_id": api_id,
                    "target_id": manual_id,
                    "type": "referenced_by",
                    "description": f"API referenced by manual section"
                })
    
    return relationships

def find_db_manual_relationships(db_docs, manual_docs):
    """Find relationships between database docs and manual docs"""
    relationships = []
    
    # For each database doc, look for references in manual docs
    for db_id, db_doc in db_docs.items():
        if db_id == "db-overview":
            continue
            
        table_name = db_doc.get("database", {}).get("tableName", "").lower()
        if not table_name:
            continue
            
        # Check each manual doc for references to this table
        for manual_id, manual_doc in manual_docs.items():
            manual_content = json.dumps(manual_doc.get("manual", {}).get("content", [])).lower()
            
            if table_name in manual_content:
                # Create relationship in both directions
                relationships.append({
                    "source_id": manual_id,
                    "target_id": db_id,
                    "type": "references",
                    "description": f"Manual section references database table"
                })
                
                relationships.append({
                    "source_id": db_id,
                    "target_id": manual_id,
                    "type": "referenced_by",
                    "description": f"Database table referenced by manual section"
                })
    
    return relationships

def find_keyword_relationships(all_docs):
    """Find relationships based on shared keywords/tags"""
    relationships = []
    
    # Flatten all docs
    all_docs_flat = {}
    for doc_type, docs in all_docs.items():
        for doc_id, doc in docs.items():
            all_docs_flat[doc_id] = doc
    
    # Build a keyword/tag index
    keyword_index = {}
    for doc_id, doc in all_docs_flat.items():
        tags = doc.get("metadata", {}).get("tags", [])
        for tag in tags:
            tag = tag.lower()
            if tag not in keyword_index:
                keyword_index[tag] = []
            keyword_index[tag].append(doc_id)
    
    # Find documents with shared keywords
    for keyword, doc_ids in keyword_index.items():
        if len(doc_ids) < 2 or keyword in ["api", "database", "manual"]:
            continue
            
        # Create relationships between documents with the same keyword
        for i in range(len(doc_ids)):
            for j in range(i+1, len(doc_ids)):
                source_id = doc_ids[i]
                target_id = doc_ids[j]
                
                # Skip if same document type (we already have those relationships)
                source_type = source_id.split("-")[0]
                target_type = target_id.split("-")[0]
                if source_type == target_type:
                    continue
                
                relationships.append({
                    "source_id": source_id,
                    "target_id": target_id,
                    "type": "related_concept",
                    "description": f"Related by concept: {keyword}"
                })
    
    return relationships

def update_docs_with_relationships(all_docs, relationships):
    """Update all documents with the new relationships"""
    # Flatten all docs for easier access
    all_docs_flat = {}
    for doc_type, docs in all_docs.items():
        all_docs_flat.update(docs)
    
    # Group relationships by source document
    doc_relationships = {}
    for rel in relationships:
        source_id = rel["source_id"]
        if source_id not in doc_relationships:
            doc_relationships[source_id] = []
        
        doc_relationships[source_id].append({
            "type": rel["type"],
            "target": rel["target_id"],
            "description": rel["description"]
        })
    
    # Update each document
    updated_count = 0
    for doc_id, new_relations in doc_relationships.items():
        if doc_id in all_docs_flat:
            doc = all_docs_flat[doc_id]
            
            # Get existing relationships
            existing_relationships = doc.get("relationships", [])
            
            # Add new relationships
            existing_targets = set(rel.get("target", "") for rel in existing_relationships)
            for new_rel in new_relations:
                # Only add if this target doesn't already exist
                if new_rel["target"] not in existing_targets:
                    existing_relationships.append(new_rel)
                    existing_targets.add(new_rel["target"])
            
            # Update the document
            doc["relationships"] = existing_relationships
            updated_count += 1
    
    return updated_count

def save_updated_docs(all_docs, base_dir):
    """Save all updated documents"""
    for doc_type, docs in all_docs.items():
        output_dir = os.path.join(base_dir, doc_type)
        for doc_id, doc in docs.items():
            output_file = os.path.join(output_dir, f"{doc_id}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2)

def generate_relationship_graph(relationships, output_file):
    """Generate a JSON graph of all relationships for visualization"""
    # Build nodes
    nodes = set()
    for rel in relationships:
        nodes.add(rel["source_id"])
        nodes.add(rel["target_id"])
    
    # Create graph
    graph = {
        "nodes": [{"id": node_id, "type": node_id.split("-")[0]} for node_id in nodes],
        "edges": [
            {
                "source": rel["source_id"],
                "target": rel["target_id"],
                "type": rel["type"]
            } for rel in relationships
        ]
    }
    
    # Save the graph
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)

def main(base_dir):
    """Main function to generate relationships between documentation"""
    # Load all processed documentation
    print("Loading processed documentation...")
    all_docs = load_processed_docs(base_dir)
    
    api_count = len(all_docs["api"])
    db_count = len(all_docs["database"])
    manual_count = len(all_docs["manual"])
    
    print(f"Loaded {api_count} API docs, {db_count} database docs, and {manual_count} manual docs")
    
    # Find relationships
    print("Finding relationships between API and Database docs...")
    api_db_relationships = find_api_db_relationships(all_docs["api"], all_docs["database"])
    
    print("Finding relationships between API and Manual docs...")
    api_manual_relationships = find_api_manual_relationships(all_docs["api"], all_docs["manual"])
    
    print("Finding relationships between Database and Manual docs...")
    db_manual_relationships = find_db_manual_relationships(all_docs["database"], all_docs["manual"])
    
    print("Finding relationships based on shared keywords...")
    keyword_relationships = find_keyword_relationships(all_docs)
    
    # Combine all relationships
    all_relationships = api_db_relationships + api_manual_relationships + db_manual_relationships + keyword_relationships
    
    print(f"Found {len(all_relationships)} relationships:")
    print(f"- API to Database: {len(api_db_relationships)}")
    print(f"- API to Manual: {len(api_manual_relationships)}")
    print(f"- Database to Manual: {len(db_manual_relationships)}")
    print(f"- Keyword-based: {len(keyword_relationships)}")
    
    # Update documents with new relationships
    print("Updating documents with relationships...")
    updated_count = update_docs_with_relationships(all_docs, all_relationships)
    print(f"Updated {updated_count} documents with new relationships")
    
    # Save updated documents
    print("Saving updated documents...")
    save_updated_docs(all_docs, base_dir)
    
    # Generate relationship graph
    print("Generating relationship graph...")
    graph_file = os.path.join(os.path.dirname(base_dir), "relationship_graph.json")
    generate_relationship_graph(all_relationships, graph_file)
    print(f"Saved relationship graph to {graph_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate relationships between documentation")
    parser.add_argument("--dir", default="/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed",
                        help="Base directory containing processed documentation")
    
    args = parser.parse_args()
    main(args.dir)
    print("Relationship generation complete!")
