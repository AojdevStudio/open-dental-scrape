#!/usr/bin/env python3
"""
process_all_docs.py - Master script to process all OpenDental documentation
"""

import os
import argparse
import subprocess
import time
import json
from pathlib import Path

def setup_directories(base_dir):
    """Create necessary directories for processed documentation"""
    dirs = [
        os.path.join(base_dir, "api"),
        os.path.join(base_dir, "database"),
        os.path.join(base_dir, "manual"),
        os.path.join(base_dir, "combined")
    ]
    
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def run_script(script_path, args=None):
    """Run a Python script with optional arguments"""
    cmd = ["python", script_path]
    if args:
        cmd.extend(args)
    
    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        end_time = time.time()
        duration = end_time - start_time
        print(f"Completed in {duration:.2f} seconds")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def combine_indices(processed_dir, output_file):
    """Create a combined index of all processed documentation"""
    api_dir = os.path.join(processed_dir, "api")
    db_dir = os.path.join(processed_dir, "database")
    manual_dir = os.path.join(processed_dir, "manual")
    
    combined_index = {
        "index": {
            "api": [],
            "database": [],
            "manual": []
        }
    }
    
    # Index API docs
    for file_path in Path(api_dir).glob("*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
            combined_index["index"]["api"].append({
                "id": doc.get("id", file_path.stem),
                "title": doc.get("title", file_path.stem),
                "path": str(file_path),
                "metadata": doc.get("metadata", {})
            })
    
    # Index database docs
    for file_path in Path(db_dir).glob("*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
            combined_index["index"]["database"].append({
                "id": doc.get("id", file_path.stem),
                "title": doc.get("title", file_path.stem),
                "path": str(file_path),
                "metadata": doc.get("metadata", {})
            })
    
    # Index manual docs
    for file_path in Path(manual_dir).glob("*.json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
            combined_index["index"]["manual"].append({
                "id": doc.get("id", file_path.stem),
                "title": doc.get("title", file_path.stem),
                "path": str(file_path),
                "metadata": doc.get("metadata", {})
            })
    
    # Save the combined index
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_index, f, indent=2)
    
    print(f"Created combined index with {len(combined_index['index']['api'])} API docs, "
          f"{len(combined_index['index']['database'])} database docs, and "
          f"{len(combined_index['index']['manual'])} manual docs")

def create_manifest(processed_dir, scripts_dir, output_file):
    """Create a manifest file with processing information"""
    manifest = {
        "processed_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_directories": {
            "api": "/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/api-documentation",
            "database": "/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/database-documentation",
            "manual": "/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/manual-documentation"
        },
        "output_directory": processed_dir,
        "scripts": {
            "api": os.path.join(scripts_dir, "process_api_docs.py"),
            "database": os.path.join(scripts_dir, "process_db_docs.py"),
            "manual": os.path.join(scripts_dir, "process_manual_docs.py"),
            "relationships": os.path.join(scripts_dir, "generate_relationships.py")
        },
        "statistics": {
            "api_files": len(list(Path(os.path.join(processed_dir, "api")).glob("*.json"))),
            "database_files": len(list(Path(os.path.join(processed_dir, "database")).glob("*.json"))),
            "manual_files": len(list(Path(os.path.join(processed_dir, "manual")).glob("*.json")))
        }
    }
    
    # Save the manifest
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Created processing manifest at {output_file}")

def main():
    """Main function to process all documentation"""
    parser = argparse.ArgumentParser(description="Process all OpenDental documentation")
    parser.add_argument("--output", default="/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed",
                        help="Output directory for processed documentation")
    parser.add_argument("--scripts", default="/Users/aojdevstudio/cursor-projects/open-dental-scrape/scripts",
                        help="Directory containing processing scripts")
    
    args = parser.parse_args()
    processed_dir = args.output
    scripts_dir = args.scripts
    
    print(f"Processing OpenDental documentation to {processed_dir}")
    
    # Create directories
    setup_directories(processed_dir)
    
    # Process API documentation
    api_script = os.path.join(scripts_dir, "process_api_docs.py")
    api_success = run_script(api_script)
    
    # Process database documentation
    db_script = os.path.join(scripts_dir, "process_db_docs.py")
    db_success = run_script(db_script)
    
    # Process manual documentation
    manual_script = os.path.join(scripts_dir, "process_manual_docs.py")
    manual_success = run_script(manual_script)
    
    # Generate relationships
    if api_success and db_success and manual_success:
        print("All documentation processed successfully, generating relationships...")
        relationships_script = os.path.join(scripts_dir, "generate_relationships.py")
        rel_success = run_script(relationships_script)
        
        if rel_success:
            print("Relationships generated successfully")
        else:
            print("WARNING: Relationship generation failed, continuing with index creation")
    else:
        print("WARNING: Some processing steps failed, skipping relationship generation")
    
    # Create combined index
    print("Creating combined index...")
    combined_index_file = os.path.join(processed_dir, "combined", "index.json")
    combine_indices(processed_dir, combined_index_file)
    
    # Create processing manifest
    print("Creating processing manifest...")
    manifest_file = os.path.join(processed_dir, "manifest.json")
    create_manifest(processed_dir, scripts_dir, manifest_file)
    
    print("\nDocumentation processing complete!")
    print(f"Processed documentation is available in {processed_dir}")
    print(f"Combined index: {combined_index_file}")
    print(f"Processing manifest: {manifest_file}")
    print("\nNext steps:")
    print("1. Review the processed files to ensure quality")
    print("2. Use these files with your vector store for AI-powered documentation access")

if __name__ == "__main__":
    main()
