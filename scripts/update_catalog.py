"""
Script to update the community dataset catalog data (docs/data/benchmark.json)
by scanning submitted assessments in the assessed_datasets/ directory.
"""

import os
import json
import yaml
import statistics
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths
ROOT_DIR = Path(__file__).parent.parent
ASSESSED_DIR = ROOT_DIR / "assessed_datasets"
OUTPUT_JSON = ROOT_DIR / "docs" / "data" / "benchmark.json"

def find_assessments(base_dir: Path) -> list:
    """Finds all metadata.yaml files recursively."""
    assessments = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower() == "metadata.yaml":
                metadata_path = Path(root) / file
                report_path = None
                # Look for any .json file in the same directory
                for sibling_file in os.listdir(root):
                    if sibling_file.lower().endswith(".json"):
                        report_path = Path(root) / sibling_file
                        break # Take the first one found

                if report_path and report_path.exists():
                    assessments.append({"metadata": metadata_path, "report": report_path})
                else:
                    logging.warning(f"Metadata found at {metadata_path} but no corresponding .json report in the same directory.")
    return assessments

def parse_assessment(metadata_path: Path, report_path: Path) -> dict | None:
    """Parses metadata and report JSON into a structured dictionary."""
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = yaml.safe_load(f)
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        # Basic validation
        required_meta = ["dataset_name", "dataset_url", "assessed_by", "assessment_date"]
        if not all(key in metadata for key in required_meta):
            logging.warning(f"Skipping {metadata_path}: Missing required metadata fields.")
            return None

        required_report = ["overall_score", "dimension_results", "source_type", "assessment_time"]
        if not all(key in report_data for key in required_report):
             logging.warning(f"Skipping {report_path}: Missing required report fields.")
             return None

        # Extract and structure data for the catalog's 'datasets' array
        dataset_entry = {
            "id": metadata_path.parent.name, # Use directory name as ID for now
            "name": metadata.get("dataset_name"),
            "description": metadata.get("dataset_description", ""),
            "industry": metadata.get("industry", "Unknown"),
            "format": report_data.get("source_type", "Unknown"),
            # Add size info if available in metadata?
            "assessment": {
                "overall_score": report_data.get("overall_score"),
                "dimension_scores": report_data.get("dimension_results", {}), # Assuming structure matches
                "timestamp": report_data.get("assessment_time"),
                "adri_version": report_data.get("adri_version"),
                # Maybe add submitter/assessment date here too?
                "assessed_by": metadata.get("assessed_by"),
                "assessment_date": str(metadata.get("assessment_date")), # Ensure string
            }
        }
        return dataset_entry

    except Exception as e:
        logging.error(f"Error parsing {metadata_path} or {report_path}: {e}")
        return None

def calculate_summaries(datasets: list) -> dict:
    """Calculates overall average, industry averages, and dimension averages."""
    summary = {
        "overall_average": 0.0,
        "industries": {},
        "dimensions": {"validity": 0.0, "completeness": 0.0, "freshness": 0.0, "consistency": 0.0, "plausibility": 0.0},
        "submissions": len(datasets)
    }
    # Keep track of scores for averaging later
    dimension_scores_lists = {k: [] for k in summary["dimensions"]}

    if not datasets:
        return summary

    all_scores = [d["assessment"]["overall_score"] for d in datasets if d.get("assessment", {}).get("overall_score") is not None]
    summary["overall_average"] = statistics.mean(all_scores) if all_scores else 0

    industry_scores = {}
    for d in datasets:
        industry = d.get("industry", "Unknown")
        score = d.get("assessment", {}).get("overall_score")
        if score is not None:
            if industry not in industry_scores:
                industry_scores[industry] = []
            industry_scores[industry].append(score)

        # Collect dimension scores into lists
        dim_scores_data = d.get("assessment", {}).get("dimension_scores", {})
        for dim_name, results in dim_scores_data.items():
            # Handle potential structure difference: results might be the score directly or a dict containing score
            dim_score = results if isinstance(results, (int, float)) else results.get("score")
            if dim_name in dimension_scores_lists and dim_score is not None:
                dimension_scores_lists[dim_name].append(dim_score)

    # Calculate averages after collecting all scores
    for industry, scores in industry_scores.items():
        summary["industries"][industry] = statistics.mean(scores) if scores else 0.0

    for dim_name, scores in dimension_scores_lists.items():
        summary["dimensions"][dim_name] = statistics.mean(scores) if scores else 0.0

    return summary


def main():
    """Main function to update the benchmark data."""
    logging.info("Starting catalog update process...")
    assessment_files = find_assessments(ASSESSED_DIR)
    logging.info(f"Found {len(assessment_files)} potential assessments.")

    all_datasets_data = []
    processed_ids = set()

    # Sort by assessment date/time to keep the latest
    assessment_files.sort(key=lambda x: Path(x["report"]).stat().st_mtime, reverse=True) # Use file mod time as proxy

    for files in assessment_files:
        parsed_data = parse_assessment(files["metadata"], files["report"])
        if parsed_data:
            dataset_id = parsed_data["id"]
            # Keep only the latest assessment per ID
            if dataset_id not in processed_ids:
                 all_datasets_data.append(parsed_data)
                 processed_ids.add(dataset_id)
            else:
                 logging.info(f"Skipping older assessment for dataset ID: {dataset_id}")


    logging.info(f"Successfully parsed {len(all_datasets_data)} unique assessments.")

    summaries = calculate_summaries(all_datasets_data)

    # Construct the final JSON structure (based on existing benchmark.json)
    output_data = {
        "updated": datetime.now().strftime("%Y-%m-%d"),
        "overall_average": round(summaries["overall_average"], 1),
        "industries": {k: round(v, 1) for k, v in summaries["industries"].items()},
        "dimensions": {k: round(v, 1) for k, v in summaries["dimensions"].items()},
        "submissions": summaries["submissions"],
        "datasets": all_datasets_data,
        # Keep other sections if they exist and are managed separately?
        # For now, assuming we only manage the core 'datasets' and summaries
        "large_file_benchmarks": [], # Placeholder
        "benchmark_datasets": {} # Placeholder
    }

    # Write the output file
    try:
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        logging.info(f"Successfully updated catalog data at {OUTPUT_JSON}")
    except Exception as e:
        logging.error(f"Failed to write output JSON: {e}")

if __name__ == "__main__":
    main()
