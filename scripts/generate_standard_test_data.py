#!/usr/bin/env python
"""Generate test data for ADRI standards.

This script takes a standard YAML file and generates:
1. Training CSV data that passes 100% validation
2. Test CSV data with intentional validation errors

The CSVs are placed in ADRI/tutorials/<standard_id>/ following the
tutorial naming convention, allowing automatic test discovery.

Usage:
    python scripts/generate_standard_test_data.py path/to/standard.yaml

The script will:
- Validate the standard structure
- Generate realistic training data (passes all rules)
- Generate test data with errors (CRITICAL and WARNING)
- Create tutorial directory
- Place CSVs for auto-discovery
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import random
import csv
from typing import Dict, Any, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adri.standards.validator import get_validator


class StandardDataGenerator:
    """Generates training and test CSV data from ADRI standard."""

    def __init__(self, standard_path: Path):
        """Initialize generator with standard file.

        Args:
            standard_path: Path to standard YAML file
        """
        self.standard_path = standard_path
        self.standard = None
        self.standard_id = None
        self.field_requirements = {}

    def load_and_validate_standard(self) -> bool:
        """Load and validate standard structure.

        Returns:
            True if valid, False otherwise
        """
        print(f"Loading standard: {self.standard_path}")

        # Validate using standard validator
        validator = get_validator()
        result = validator.validate_standard_file(str(self.standard_path))

        if not result.is_valid:
            print(f"✗ Standard validation failed:")
            print(result.format_errors())
            return False

        # Load the standard
        with open(self.standard_path, 'r', encoding='utf-8') as f:
            self.standard = yaml.safe_load(f)

        # Extract standard ID
        self.standard_id = self.standard['standards']['id']

        # Extract field requirements
        requirements = self.standard.get('requirements', {})
        self.field_requirements = requirements.get('field_requirements', {})

        if not self.field_requirements:
            print(f"✗ No field_requirements found in standard")
            return False

        print(f"✓ Standard validated: {self.standard_id}")
        print(f"  Fields: {len(self.field_requirements)}")

        return True

    def generate_training_data(self, num_rows: int = 5) -> List[Dict[str, Any]]:
        """Generate training data that passes all validation rules.

        Args:
            num_rows: Number of rows to generate

        Returns:
            List of dictionaries representing CSV rows
        """
        print(f"\nGenerating training data ({num_rows} rows)...")

        rows = []
        for i in range(num_rows):
            row = {}
            for field_name, field_config in self.field_requirements.items():
                value = self._generate_valid_value(field_name, field_config, i)
                row[field_name] = value
            rows.append(row)

        print(f"✓ Generated {len(rows)} training rows")
        return rows

    def generate_test_data(self, num_rows: int = 5) -> List[Dict[str, Any]]:
        """Generate test data with intentional validation errors.

        Args:
            num_rows: Number of rows to generate

        Returns:
            List of dictionaries representing CSV rows with errors
        """
        print(f"\nGenerating test data with errors ({num_rows} rows)...")

        rows = []
        error_count = 0

        for i in range(num_rows):
            row = {}

            # Decide which fields to make invalid (25-50% of fields per row)
            fields_to_invalidate = random.sample(
                list(self.field_requirements.keys()),
                k=random.randint(
                    max(1, len(self.field_requirements) // 4),
                    max(1, len(self.field_requirements) // 2)
                )
            )

            for field_name, field_config in self.field_requirements.items():
                if field_name in fields_to_invalidate:
                    # Generate invalid value
                    value = self._generate_invalid_value(field_name, field_config, i)
                    error_count += 1
                else:
                    # Generate valid value
                    value = self._generate_valid_value(field_name, field_config, i)

                row[field_name] = value

            rows.append(row)

        print(f"✓ Generated {len(rows)} test rows with ~{error_count} errors")
        return rows

    def _generate_valid_value(self, field_name: str, field_config: Dict, index: int) -> Any:
        """Generate a valid value for a field.

        Args:
            field_name: Name of the field
            field_config: Field configuration from standard
            index: Row index for variation

        Returns:
            Valid value for the field
        """
        field_type = field_config.get('type', 'string')
        nullable = field_config.get('nullable', False)

        # Handle nullable fields (occasionally return null/empty)
        if nullable and index % 10 == 0:
            return ''

        if field_type == 'string':
            return self._generate_valid_string(field_name, field_config, index)
        elif field_type in ['integer', 'number', 'float']:
            return self._generate_valid_number(field_name, field_config, index)
        elif field_type == 'date':
            return self._generate_valid_date(field_name, field_config, index)
        elif field_type == 'boolean':
            return random.choice(['true', 'false'])
        else:
            return f"value_{index}"

    def _generate_valid_string(self, field_name: str, field_config: Dict, index: int) -> str:
        """Generate valid string value."""
        # Check for allowed_values
        allowed_values = field_config.get('allowed_values') or field_config.get('valid_values')
        if allowed_values:
            return random.choice(allowed_values)

        # Check for pattern
        pattern = field_config.get('pattern', '')
        if 'email' in field_name.lower() or '@' in pattern:
            return f"user{index}@example.com"
        elif 'phone' in field_name.lower():
            return f"555-{1000 + index:04d}"
        elif 'id' in field_name.lower() or 'key' in field_name.lower():
            return f"{field_name.upper()}-{1000 + index:05d}"
        elif 'url' in field_name.lower() or 'http' in pattern:
            return f"https://example.com/resource/{index}"
        else:
            # Generate based on min/max length if specified
            min_length = field_config.get('min_length', 5)
            max_length = field_config.get('max_length', 50)
            length = min(max_length, max(min_length, 10))
            return f"{field_name}_value_{index}".ljust(length, 'x')[:length]

    def _generate_valid_number(self, field_name: str, field_config: Dict, index: int) -> float:
        """Generate valid numeric value."""
        min_value = field_config.get('min_value', 0)
        max_value = field_config.get('max_value', 1000)

        field_type = field_config.get('type')

        if field_type == 'integer':
            return random.randint(int(min_value), int(max_value))
        else:
            return round(random.uniform(float(min_value), float(max_value)), 2)

    def _generate_valid_date(self, field_name: str, field_config: Dict, index: int) -> str:
        """Generate valid date value."""
        # Generate dates in the past year
        base_date = datetime.now() - timedelta(days=365)
        date_value = base_date + timedelta(days=index * 7)

        # Check pattern for format
        pattern = field_config.get('pattern', '')
        if 'T' in pattern:
            # ISO 8601 datetime
            return date_value.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            # Simple date
            return date_value.strftime('%Y-%m-%d')

    def _generate_invalid_value(self, field_name: str, field_config: Dict, index: int) -> Any:
        """Generate an invalid value that will fail validation.

        Args:
            field_name: Name of the field
            field_config: Field configuration from standard
            index: Row index for variation

        Returns:
            Invalid value that should trigger validation errors
        """
        field_type = field_config.get('type', 'string')
        nullable = field_config.get('nullable', False)

        # Strategy: violate different types of rules
        violation_type = random.choice(['null', 'type', 'range', 'pattern', 'length'])

        if violation_type == 'null' and not nullable:
            return ''
        elif violation_type == 'type':
            return 'INVALID_TYPE'
        elif field_type in ['integer', 'number', 'float']:
            # Violate numeric bounds
            min_value = field_config.get('min_value')
            max_value = field_config.get('max_value')
            if min_value is not None:
                return min_value - 10
            elif max_value is not None:
                return max_value + 10
            else:
                return -9999
        elif field_type == 'string':
            # Violate string constraints
            allowed_values = field_config.get('allowed_values') or field_config.get('valid_values')
            if allowed_values:
                return 'INVALID_VALUE'

            min_length = field_config.get('min_length')
            max_length = field_config.get('max_length')
            if min_length:
                return 'x' * (min_length - 1) if min_length > 1 else ''
            elif max_length:
                return 'x' * (max_length + 10)
            else:
                return 'INVALID'
        elif field_type == 'date':
            return 'NOT-A-DATE'
        else:
            return 'INVALID'

    def create_tutorial_directory(self) -> Path:
        """Create tutorial directory for the standard.

        Returns:
            Path to created directory
        """
        # Get project root
        project_root = self.standard_path.parent
        while not (project_root / 'ADRI').exists() and project_root.parent != project_root:
            project_root = project_root.parent

        # Create tutorial directory
        tutorial_dir = project_root / 'ADRI' / 'tutorials' / self.standard_id
        tutorial_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n✓ Created tutorial directory: {tutorial_dir.relative_to(project_root)}")
        return tutorial_dir

    def write_csv_files(self, tutorial_dir: Path, training_data: List[Dict], test_data: List[Dict]):
        """Write training and test CSV files.

        Args:
            tutorial_dir: Directory to write files to
            training_data: Training data rows
            test_data: Test data rows
        """
        # Training CSV
        training_path = tutorial_dir / f"{self.standard_id}_data.csv"
        self._write_csv(training_path, training_data)
        print(f"✓ Wrote training data: {training_path.name}")

        # Test CSV
        test_path = tutorial_dir / f"test_{self.standard_id}_data.csv"
        self._write_csv(test_path, test_data)
        print(f"✓ Wrote test data: {test_path.name}")

    def _write_csv(self, path: Path, data: List[Dict]):
        """Write data to CSV file.

        Args:
            path: Path to write to
            data: List of dictionaries
        """
        if not data:
            return

        fieldnames = list(data[0].keys())

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_standard_test_data.py <standard.yaml>")
        print("\nExample:")
        print("  python scripts/generate_standard_test_data.py adri/standards/domains/customer_service_standard.yaml")
        sys.exit(1)

    standard_path = Path(sys.argv[1])

    if not standard_path.exists():
        print(f"✗ Standard file not found: {standard_path}")
        sys.exit(1)

    print("=" * 70)
    print("ADRI Standard Test Data Generator")
    print("=" * 70)

    generator = StandardDataGenerator(standard_path)

    # Step 1: Load and validate
    if not generator.load_and_validate_standard():
        sys.exit(1)

    # Step 2: Generate data
    training_data = generator.generate_training_data(num_rows=5)
    test_data = generator.generate_test_data(num_rows=5)

    # Step 3: Create tutorial directory
    tutorial_dir = generator.create_tutorial_directory()

    # Step 4: Write CSV files
    generator.write_csv_files(tutorial_dir, training_data, test_data)

    print("\n" + "=" * 70)
    print("✓ Test data generation complete!")
    print("=" * 70)
    print(f"\nNext steps:")
    print(f"1. Review generated CSV files in: {tutorial_dir.name}/")
    print(f"2. Run tutorial tests:")
    print(f"   pytest tests/test_tutorial_auto_discovery.py -v -k {generator.standard_id}")
    print("\nThe tutorial discovery system will automatically find and test this standard!")

    return 0


if __name__ == '__main__':
    sys.exit(main())
