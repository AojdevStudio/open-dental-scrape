#!/usr/bin/env python3
"""
process_manual_docs.py - Process OpenDental manual documentation from JSON and convert to structured format
"""

import os
import json
import argparse
import re
from pathlib import Path

def extract_sections(manual_content):
    """Extract hierarchical sections from the manual content"""
    sections = []
    current_section = None
    current_subsection = None
    current_topic = None
    current_content = []
    
    for item in manual_content["Manual"]:
        if item["type"] == "heading1":
            # Save previous section if exists
            if current_section and current_content:
                sections.append({
                    "section": current_section,
                    "subsection": current_subsection,
                    "topic": current_topic,
                    "content": current_content
                })
            
            # Start new section
            current_section = item["text"]
            current_subsection = None
            current_topic = None
            current_content = []
        
        elif item["type"] == "heading2":
            # Save previous subsection if exists
            if current_section and current_content:
                sections.append({
                    "section": current_section,
                    "subsection": current_subsection,
                    "topic": current_topic,
                    "content": current_content
                })
            
            # Start new subsection
            current_subsection = item["text"]
            current_topic = None
            current_content = []
        
        elif item["type"] == "heading3":
            # Save previous topic if exists
            if current_section and current_content:
                sections.append({
                    "section": current_section,
                    "subsection": current_subsection,
                    "topic": current_topic,
                    "content": current_content
                })
            
            # Start new topic
            current_topic = item["text"]
            current_content = []
        
        else:
            # Add content to current section/subsection/topic
            current_content.append(item)
    
    # Add the last section
    if current_section and current_content:
        sections.append({
            "section": current_section,
            "subsection": current_subsection,
            "topic": current_topic,
            "content": current_content
        })
    
    return sections

def process_section_content(content):
    """Process and structure the content items of a section"""
    processed_content = []
    
    for item in content:
        content_type = item["type"]
        
        if content_type == "paragraph":
            processed_content.append({
                "type": "text",
                "content": item["text"]
            })
        
        elif content_type == "list":
            processed_content.append({
                "type": "list",
                "items": item.get("items", []),
                "ordered": item.get("ordered", False)
            })
        
        elif content_type == "image":
            processed_content.append({
                "type": "image",
                "url": item.get("url", ""),
                "alt": item.get("alt", ""),
                "caption": item.get("caption", "")
            })
        
        elif content_type == "note" or content_type == "warning":
            processed_content.append({
                "type": content_type,
                "content": item.get("text", "")
            })
        
        elif content_type == "code":
            processed_content.append({
                "type": "code",
                "language": item.get("language", ""),
                "content": item.get("text", "")
            })
        
        else:
            # Default handling for other content types
            processed_content.append({
                "type": "text",
                "content": item.get("text", "Unknown content")
            })
    
    return processed_content

def extract_related_topics(section):
    """Extract related topics from section content"""
    related = []
    
    # Look for "See Also", "Related", or similar phrases
    related_patterns = [
        r"See also(?::|\.)\s*([^\.]+)",
        r"Related(?::|\.)\s*([^\.]+)",
        r"For more information(?::|,)\s*see\s*([^\.]+)"
    ]
    
    # Join all text content for searching
    text_content = " ".join([
        item.get("content", "") 
        for item in section.get("processed_content", [])
        if item.get("type") == "text"
    ])
    
    for pattern in related_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        for match in matches:
            # Extract individual topics
            topics = re.findall(r"([A-Za-z\s]+(?:\([A-Za-z\s]+\))?)", match)
            related.extend([topic.strip() for topic in topics if topic.strip()])
    
    return related

def extract_keywords(section):
    """Extract keywords from section content"""
    # Combine all text
    text_content = " ".join([
        item.get("content", "") 
        for item in section.get("processed_content", [])
        if item.get("type") == "text"
    ])
    
    # Common dental software terms to look for
    dental_terms = [
        "patient", "appointment", "provider", "insurance", "claim", 
        "procedure", "chart", "recall", "billing", "schedule",
        "treatment", "prescription", "payment", "lab", "imaging"
    ]
    
    # Find matches
    keywords = []
    for term in dental_terms:
        if re.search(r"\b" + re.escape(term) + r"\b", text_content, re.IGNORECASE):
            keywords.append(term.capitalize())
    
    # Add section/subsection/topic as keywords
    if section["section"]:
        keywords.append(section["section"])
    if section["subsection"]:
        keywords.append(section["subsection"])
    if section["topic"]:
        keywords.append(section["topic"])
    
    return list(set(keywords))  # Remove duplicates

def create_doc_id(section, subsection, topic):
    """Create a document ID from section information"""
    components = []
    
    if section:
        components.append(section.lower().replace(" ", "-"))
    if subsection:
        components.append(subsection.lower().replace(" ", "-"))
    if topic:
        components.append(topic.lower().replace(" ", "-"))
    
    # Ensure we have at least one component
    if not components:
        components = ["unknown"]
    
    return "manual-" + "-".join(components)

def process_manual_docs(input_file, output_dir):
    """Process manual documentation JSON and convert to structured format"""
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        manual_content = json.load(f)
    
    # Extract sections
    sections = extract_sections(manual_content)
    print(f"Found {len(sections)} sections in the manual")
    
    # Process each section
    processed_sections = []
    for section in sections:
        # Skip empty sections
        if not section["content"]:
            continue
        
        # Process content
        section["processed_content"] = process_section_content(section["content"])
        
        # Extract related topics and keywords
        section["related_topics"] = extract_related_topics(section)
        section["keywords"] = extract_keywords(section)
        
        processed_sections.append(section)
    
    # Create structured documents
    for section in processed_sections:
        doc_id = create_doc_id(section["section"], section["subsection"], section["topic"])
        
        # Create document title
        if section["topic"]:
            title = section["topic"]
        elif section["subsection"]:
            title = section["subsection"]
        else:
            title = section["section"]
        
        # Build the path
        path_components = []
        if section["section"]:
            path_components.append(section["section"])
        if section["subsection"]:
            path_components.append(section["subsection"])
        if section["topic"]:
            path_components.append(section["topic"])
        
        path = " > ".join(path_components)
        
        # Create structured document
        manual_doc = {
            "id": doc_id,
            "type": "manual",
            "title": title,
            "path": path,
            "metadata": {
                "category": ["Manual"],
                "tags": section["keywords"],
                "section": section["section"],
                "subsection": section["subsection"],
                "topic": section["topic"]
            },
            "manual": {
                "content": section["processed_content"]
            },
            "relationships": [
                {
                    "type": "related",
                    "target": create_doc_id(None, None, topic),
                    "description": "Related topic"
                } for topic in section["related_topics"]
            ]
        }
        
        # Save the structured JSON
        output_file = os.path.join(output_dir, f"{doc_id}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(manual_doc, f, indent=2)
        
        print(f"Processed: {title} -> {os.path.basename(output_file)}")
    
    # Create manual TOC
    toc = {
        "id": "manual-toc",
        "type": "manual",
        "title": "Manual Table of Contents",
        "metadata": {
            "category": ["Manual", "Overview"],
            "tags": ["Table of Contents", "Overview", "Navigation"]
        },
        "manual": {
            "content": [
                {
                    "type": "text",
                    "content": "OpenDental Manual Table of Contents"
                },
                {
                    "type": "toc",
                    "sections": [
                        {
                            "section": section["section"],
                            "subsection": section["subsection"],
                            "topic": section["topic"],
                            "id": create_doc_id(section["section"], section["subsection"], section["topic"])
                        } for section in processed_sections
                    ]
                }
            ]
        },
        "relationships": [
            {
                "type": "contains",
                "target": create_doc_id(section["section"], section["subsection"], section["topic"]),
                "description": f"Contains section {section['section']}"
            } for section in processed_sections
        ]
    }
    
    # Save the TOC
    toc_file = os.path.join(output_dir, "manual-toc.json")
    with open(toc_file, 'w', encoding='utf-8') as f:
        json.dump(toc, f, indent=2)
    
    print(f"Created manual table of contents -> {os.path.basename(toc_file)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process OpenDental manual documentation")
    parser.add_argument("--input", default="/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/manual-documentation/manual_content.json",
                        help="Input manual documentation JSON file")
    parser.add_argument("--output", default="/Users/aojdevstudio/cursor-projects/open-dental-scrape/docs/processed/manual",
                        help="Output directory for structured JSON files")
    
    args = parser.parse_args()
    process_manual_docs(args.input, args.output)
    print("Manual documentation processing complete!")
