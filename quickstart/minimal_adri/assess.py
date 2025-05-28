#!/usr/bin/env python3
"""
Minimal ADRI implementation using only Python standard library.
This demonstrates core ADRI concepts without external dependencies.
"""

import csv
import json
from datetime import datetime, timedelta
from collections import defaultdict

class MinimalADRI:
    """Simplified ADRI assessor for demonstration purposes."""
    
    def __init__(self):
        self.issues = {
            'validity': [],
            'completeness': [],
            'freshness': [],
            'consistency': [],
            'plausibility': []
        }
        self.stats = {}
        
    def assess_csv(self, csv_file):
        """Run a simplified assessment on a CSV file."""
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        self.stats['total_rows'] = len(rows)
        self.stats['columns'] = list(rows[0].keys()) if rows else []
        
        # Run dimension checks
        self._check_validity(rows)
        self._check_completeness(rows)
        self._check_freshness(rows)
        self._check_consistency(rows)
        self._check_plausibility(rows)
        
        return self._generate_report(rows)
    
    def _check_validity(self, rows):
        """Check for valid data formats."""
        for i, row in enumerate(rows):
            # Check numeric fields
            for field in ['price', 'quantity', 'amount', 'score']:
                if field in row and row[field]:
                    try:
                        float(row[field])
                    except ValueError:
                        self.issues['validity'].append({
                            'row': i + 1,
                            'field': field,
                            'value': row[field],
                            'issue': f"Invalid number format"
                        })
            
            # Check date fields
            for field in ['date', 'purchase_date', 'created_at', 'updated_at']:
                if field in row and row[field]:
                    if not self._is_valid_date(row[field]):
                        self.issues['validity'].append({
                            'row': i + 1,
                            'field': field,
                            'value': row[field],
                            'issue': f"Invalid date format"
                        })
    
    def _check_completeness(self, rows):
        """Check for missing data."""
        if not rows:
            return
            
        # Count missing values per column
        missing_counts = defaultdict(int)
        for row in rows:
            for field, value in row.items():
                if not value or value.strip() == '':
                    missing_counts[field] += 1
        
        # Report fields with significant missing data
        for field, count in missing_counts.items():
            pct_missing = (count / len(rows)) * 100
            if pct_missing > 10:  # More than 10% missing
                self.issues['completeness'].append({
                    'field': field,
                    'missing_count': count,
                    'percentage': round(pct_missing, 1),
                    'issue': f"{pct_missing:.1f}% of values are missing"
                })
    
    def _check_freshness(self, rows):
        """Check data recency."""
        date_fields = ['date', 'purchase_date', 'created_at', 'updated_at']
        today = datetime.now()
        
        for field in date_fields:
            if not rows or field not in rows[0]:
                continue
                
            dates = []
            for row in rows:
                if row.get(field):
                    try:
                        # Try common date formats
                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                            try:
                                date = datetime.strptime(row[field], fmt)
                                dates.append(date)
                                break
                            except ValueError:
                                continue
                    except:
                        pass
            
            if dates:
                newest = max(dates)
                oldest = min(dates)
                days_old = (today - newest).days
                
                if days_old > 30:
                    self.issues['freshness'].append({
                        'field': field,
                        'newest_date': newest.strftime('%Y-%m-%d'),
                        'days_old': days_old,
                        'issue': f"Most recent data is {days_old} days old"
                    })
    
    def _check_consistency(self, rows):
        """Check for inconsistent data."""
        # Example: Check if related fields are consistent
        for i, row in enumerate(rows):
            # Price and quantity consistency
            if 'price' in row and 'quantity' in row and 'total' in row:
                try:
                    price = float(row['price'])
                    quantity = float(row['quantity'])
                    total = float(row['total'])
                    expected = price * quantity
                    if abs(total - expected) > 0.01:
                        self.issues['consistency'].append({
                            'row': i + 1,
                            'issue': f"Total ({total}) doesn't match price×quantity ({expected:.2f})"
                        })
                except:
                    pass
    
    def _check_plausibility(self, rows):
        """Check for implausible values."""
        # Collect numeric values for outlier detection
        numeric_fields = defaultdict(list)
        
        for row in rows:
            for field in ['price', 'quantity', 'amount', 'score']:
                if field in row and row[field]:
                    try:
                        value = float(row[field])
                        numeric_fields[field].append(value)
                    except:
                        pass
        
        # Simple outlier detection
        for field, values in numeric_fields.items():
            if len(values) < 5:
                continue
                
            mean = sum(values) / len(values)
            sorted_values = sorted(values)
            
            # Check for negative values where they don't make sense
            if field in ['price', 'quantity', 'amount'] and min(values) < 0:
                self.issues['plausibility'].append({
                    'field': field,
                    'issue': f"Found negative values in {field}"
                })
            
            # Check for extreme outliers (simple method)
            if max(values) > mean * 10:
                self.issues['plausibility'].append({
                    'field': field,
                    'issue': f"Found extreme outliers (max: {max(values)}, mean: {mean:.2f})"
                })
    
    def _is_valid_date(self, date_str):
        """Check if string is a valid date."""
        if not date_str:
            return False
            
        # Try common date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        return False
    
    def _generate_report(self, rows):
        """Generate a simplified report."""
        # Calculate dimension scores (simplified)
        scores = {}
        for dimension in self.issues:
            if dimension == 'completeness':
                # Based on percentage of complete fields
                total_cells = len(rows) * len(self.stats['columns']) if rows else 1
                missing_cells = sum(issue['missing_count'] for issue in self.issues[dimension])
                scores[dimension] = max(0, 100 - (missing_cells / total_cells * 100))
            else:
                # Simple penalty-based scoring
                penalty = len(self.issues[dimension]) * 5
                scores[dimension] = max(0, 100 - penalty)
        
        overall_score = sum(scores.values()) / len(scores) if scores else 0
        
        return {
            'overall_score': round(overall_score, 1),
            'dimension_scores': scores,
            'issues': self.issues,
            'stats': self.stats
        }
    
    def format_report(self, report):
        """Format report for display."""
        lines = []
        lines.append("=" * 60)
        lines.append("ADRI ASSESSMENT REPORT (Minimal Version)")
        lines.append("=" * 60)
        lines.append(f"\nOverall Score: {report['overall_score']}/100")
        lines.append("\nDimension Scores:")
        
        for dim, score in report['dimension_scores'].items():
            lines.append(f"  - {dim.capitalize()}: {score:.1f}/100")
        
        lines.append(f"\nTotal Rows Analyzed: {report['stats']['total_rows']}")
        
        # Show top issues
        lines.append("\n" + "=" * 60)
        lines.append("KEY FINDINGS:")
        lines.append("=" * 60)
        
        issue_count = 0
        for dimension, issues in report['issues'].items():
            if issues:
                lines.append(f"\n{dimension.upper()}:")
                for issue in issues[:3]:  # Show top 3 issues per dimension
                    issue_count += 1
                    if 'field' in issue:
                        lines.append(f"  - {issue['field']}: {issue['issue']}")
                    else:
                        lines.append(f"  - {issue['issue']}")
                
                if len(issues) > 3:
                    lines.append(f"  ... and {len(issues) - 3} more issues")
        
        if issue_count == 0:
            lines.append("\nNo significant issues found!")
        
        return "\n".join(lines)


def main():
    """Run minimal assessment on provided CSV file."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python assess.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    try:
        assessor = MinimalADRI()
        report = assessor.assess_csv(csv_file)
        print(assessor.format_report(report))
        
        # Save JSON report
        json_file = csv_file.replace('.csv', '_minimal.json')
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {json_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
