"""
Script to collect assessment results and update the benchmark data.
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path
import statistics


def update_benchmark_data():
    """Update benchmark data based on collected assessment results."""
    print("Updating benchmark data...")
    
    # Directory where anonymous submissions are stored
    benchmark_dir = Path("benchmark/data")
    output_file = Path("docs/data/benchmark.json")
    
    # Ensure directories exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing benchmark data if it exists
    if output_file.exists():
        with open(output_file, 'r') as f:
            benchmark_data = json.load(f)
    else:
        benchmark_data = {
            "updated": datetime.now().strftime("%Y-%m-%d"),
            "overall_average": 0,
            "industries": {},
            "dimensions": {
                "validity": 0,
                "completeness": 0,
                "freshness": 0,
                "consistency": 0,
                "plausibility": 0
            },
            "submissions": 0
        }
    
    # Find all assessment files
    assessment_files = glob.glob(str(benchmark_dir / "*.json"))
    
    if not assessment_files:
        print("No assessment files found.")
        return
    
    # Parse and aggregate data
    all_scores = []
    industry_scores = {}
    dimension_scores = {
        "validity": [],
        "completeness": [],
        "freshness": [],
        "consistency": [],
        "plausibility": []
    }
    
    for file_path in assessment_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract overall score
            overall_score = data.get("overall_score", 0)
            all_scores.append(overall_score)
            
            # Extract industry
            industry = data.get("source_metadata", {}).get("industry", "Unknown")
            if industry not in industry_scores:
                industry_scores[industry] = []
            industry_scores[industry].append(overall_score)
            
            # Extract dimension scores
            for dim_name, dim_results in data.get("dimension_results", {}).items():
                if dim_name in dimension_scores:
                    dimension_scores[dim_name].append(dim_results.get("score", 0))
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Calculate averages
    benchmark_data["updated"] = datetime.now().strftime("%Y-%m-%d")
    benchmark_data["submissions"] = len(all_scores)
    
    if all_scores:
        benchmark_data["overall_average"] = round(statistics.mean(all_scores), 1)
    
    # Update industry averages
    for industry, scores in industry_scores.items():
        if scores:
            benchmark_data["industries"][industry] = round(statistics.mean(scores), 1)
    
    # Update dimension averages
    for dim_name, scores in dimension_scores.items():
        if scores:
            benchmark_data["dimensions"][dim_name] = round(statistics.mean(scores), 1)
    
    # Save updated benchmark data
    with open(output_file, 'w') as f:
        json.dump(benchmark_data, f, indent=2)
    
    print(f"Benchmark data updated with {len(all_scores)} submissions.")
    print(f"Overall average score: {benchmark_data['overall_average']}")


if __name__ == "__main__":
    update_benchmark_data()
