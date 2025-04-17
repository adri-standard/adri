#!/usr/bin/env python3
"""
Migration script to reorganize dataset assessments from the old structure to the new one.

This script:
1. Creates domain-specific directories in datasets/ based on industry
2. Moves assessment files from assessed_datasets/ to the appropriate domain directory
3. Updates references if needed
"""

import os
import json
import yaml
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths
ROOT_DIR = Path(__file__).parent.parent
OLD_DATASET_DIR = ROOT_DIR / "assessed_datasets"
NEW_DATASET_DIR = ROOT_DIR / "datasets"

# Industry to directory mapping
INDUSTRY_DIRS = {
    "Finance": "financial",
    "Financial": "financial", 
    "Banking": "financial",
    "Healthcare": "healthcare",
    "Medical": "healthcare",
    "E-commerce": "ecommerce",
    "Retail": "ecommerce",
    "Transportation": "transportation",
    "Travel": "transportation",
    "Energy": "energy",
    "Utilities": "energy",
    "Education": "education",
    "Technology": "technology",
    "Tech": "technology",
    "Media": "media",
    "Entertainment": "media",
    "Government": "government",
    "Public Sector": "government",
    "Manufacturing": "manufacturing",
    "Unknown": "general"
    # Add more mappings as needed
}

def create_domain_directories():
    """Create domain-specific directories based on industry mapping."""
    created_dirs = set()
    
    for _, dir_name in INDUSTRY_DIRS.items():
        if dir_name not in created_dirs:
            domain_dir = NEW_DATASET_DIR / dir_name
            domain_dir.mkdir(exist_ok=True)
            created_dirs.add(dir_name)
            logging.info(f"Created directory: {domain_dir}")
            
    return created_dirs
            
def get_dataset_industry(dataset_dir: Path) -> str:
    """Determine the industry of a dataset from its metadata."""
    metadata_path = dataset_dir / "metadata.yaml"
    if not metadata_path.exists():
        return "Unknown"
        
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = yaml.safe_load(f)
        industry = metadata.get("industry", "Unknown")
        return industry
    except Exception as e:
        logging.error(f"Error reading metadata for {dataset_dir}: {e}")
        return "Unknown"
        
def map_industry_to_directory(industry: str) -> str:
    """Map an industry to its directory."""
    industry_key = industry.strip()
    return INDUSTRY_DIRS.get(industry_key, "general")
    
def migrate_datasets():
    """Migrate datasets from old structure to the new domain-specific structure."""
    if not OLD_DATASET_DIR.exists():
        logging.warning(f"Old dataset directory not found: {OLD_DATASET_DIR}")
        return
        
    dataset_dirs = [d for d in OLD_DATASET_DIR.iterdir() if d.is_dir()]
    logging.info(f"Found {len(dataset_dirs)} datasets to migrate")
    
    for dataset_dir in dataset_dirs:
        industry = get_dataset_industry(dataset_dir)
        domain = map_industry_to_directory(industry)
        
        # Create target directory
        target_dir = NEW_DATASET_DIR / domain / dataset_dir.name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all files from old directory to new
        for item in dataset_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, target_dir / item.name)
                logging.info(f"Copied {item} to {target_dir / item.name}")
                
        logging.info(f"Migrated dataset '{dataset_dir.name}' to {domain} domain")
    
    logging.info("Dataset migration complete")
    
def main():
    """Main function to migrate datasets."""
    logging.info("Starting dataset migration...")
    
    # Create domain directories
    create_domain_directories()
    
    # Migrate datasets
    migrate_datasets()
    
    # Update catalog
    try:
        import update_catalog
        logging.info("Running update_catalog.py to update benchmark.json with new dataset locations...")
        update_catalog.main()
    except Exception as e:
        logging.error(f"Error updating catalog: {e}")
    
    logging.info("Migration completed successfully")
    
if __name__ == "__main__":
    main()
