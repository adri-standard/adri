#!/usr/bin/env python3
"""
Batch processor for flake8 errors with Cline-compatible interface.

Processes flake8 errors in manageable batches to prevent interface overload
while providing incremental progress reporting and fix capabilities.
"""

import os
import sys
import time
import yaml
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add the parent directory to the path to import error_categorizer
sys.path.append(str(Path(__file__).parent))
from error_categorizer import ErrorCategorizer, FlakeError, ErrorCategory, ErrorSeverity


@dataclass
class BatchResult:
    """Result of processing a batch of errors."""
    batch_id: int
    category: ErrorCategory
    errors_processed: int
    errors_fixed: int
    errors_failed: int
    files_modified: List[str]
    processing_time: float
    success: bool
    error_details: List[str]


class BatchReporter:
    """Progress reporting utilities for batch processing."""
    
    def __init__(self, config: Dict, log_to_file: bool = True):
        """
        Initialize the batch reporter.
        
        Args:
            config: Configuration dictionary
            log_to_file: Whether to log to file
        """
        self.config = config
        self.log_to_file = log_to_file
        self.start_time = datetime.now()
        self.batch_results = []
        
        # Set up logging
        self._setup_logging()
        
        # Ensure log directory exists
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
    
    def _setup_logging(self):
        """Set up logging configuration."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_format = log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s')
        
        # Configure main logger
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_config.get('main_log', 'logs/flake8_batch.log'))
            ] if self.log_to_file else [logging.StreamHandler()]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def report_session_start(self, total_errors: int, categories: Dict[ErrorCategory, int]):
        """
        Report the start of a batch processing session.
        
        Args:
            total_errors: Total number of errors to process
            categories: Dictionary mapping categories to error counts
        """
        print(f"\n🔧 Starting Flake8 Batch Processing Session")
        print(f"📊 Total errors found: {total_errors}")
        print(f"⏰ Session started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📋 Error Categories:")
        for category, count in categories.items():
            print(f"  • {category.value}: {count} errors")
        
        self.logger.info(f"Batch processing session started with {total_errors} total errors")
    
    def report_batch_start(self, batch_id: int, category: ErrorCategory, errors: List[FlakeError]):
        """
        Report the start of processing a batch.
        
        Args:
            batch_id: Batch identifier
            category: Error category being processed
            errors: List of errors in this batch
        """
        print(f"\n🚀 Processing Batch #{batch_id}")
        print(f"📂 Category: {category.value}")
        print(f"🔢 Errors in batch: {len(errors)}")
        
        # Show first few errors in the batch
        print(f"📝 Sample errors:")
        for i, error in enumerate(errors[:3]):
            print(f"  {i+1}. {error.file_path}:{error.line_number} - {error.error_code}: {error.error_message}")
        
        if len(errors) > 3:
            print(f"  ... and {len(errors) - 3} more errors")
        
        self.logger.info(f"Starting batch {batch_id} with {len(errors)} {category.value} errors")
    
    def report_batch_progress(self, batch_id: int, current: int, total: int, current_file: str):
        """
        Report progress within a batch.
        
        Args:
            batch_id: Batch identifier
            current: Current error being processed
            total: Total errors in batch
            current_file: File currently being processed
        """
        progress_pct = (current / total) * 100
        progress_bar = "█" * int(progress_pct // 10) + "░" * (10 - int(progress_pct // 10))
        
        print(f"⚡ Batch #{batch_id} Progress: [{progress_bar}] {progress_pct:.1f}% ({current}/{total})")
        print(f"📄 Current file: {current_file}")
        
        # Only log major progress milestones to avoid log spam
        if current % 5 == 0 or current == total:
            self.logger.info(f"Batch {batch_id} progress: {current}/{total} ({progress_pct:.1f}%)")
    
    def report_batch_complete(self, result: BatchResult):
        """
        Report the completion of a batch.
        
        Args:
            result: BatchResult object with processing details
        """
        self.batch_results.append(result)
        
        # Success indicators
        success_icon = "✅" if result.success else "❌"
        fix_rate = (result.errors_fixed / result.errors_processed * 100) if result.errors_processed > 0 else 0
        
        print(f"\n{success_icon} Batch #{result.batch_id} Complete")
        print(f"📊 Results:")
        print(f"  • Errors processed: {result.errors_processed}")
        print(f"  • Errors fixed: {result.errors_fixed}")
        print(f"  • Errors failed: {result.errors_failed}")
        print(f"  • Fix rate: {fix_rate:.1f}%")
        print(f"  • Files modified: {len(result.files_modified)}")
        print(f"  • Processing time: {result.processing_time:.2f}s")
        
        # Show modified files
        if result.files_modified:
            print(f"📝 Files modified:")
            for file_path in result.files_modified[:5]:  # Show max 5 files
                print(f"  • {file_path}")
            if len(result.files_modified) > 5:
                print(f"  ... and {len(result.files_modified) - 5} more files")
        
        # Show any error details
        if result.error_details:
            print(f"⚠️  Errors encountered:")
            for error_detail in result.error_details[:3]:  # Show max 3 errors
                print(f"  • {error_detail}")
            if len(result.error_details) > 3:
                print(f"  ... and {len(result.error_details) - 3} more errors")
        
        self.logger.info(f"Batch {result.batch_id} completed: {result.errors_fixed}/{result.errors_processed} fixed")
    
    def report_session_summary(self):
        """Report the final summary of the batch processing session."""
        end_time = datetime.now()
        total_time = (end_time - self.start_time).total_seconds()
        
        # Calculate totals
        total_batches = len(self.batch_results)
        total_processed = sum(r.errors_processed for r in self.batch_results)
        total_fixed = sum(r.errors_fixed for r in self.batch_results)
        total_failed = sum(r.errors_failed for r in self.batch_results)
        successful_batches = sum(1 for r in self.batch_results if r.success)
        
        # Calculate rates
        fix_rate = (total_fixed / total_processed * 100) if total_processed > 0 else 0
        success_rate = (successful_batches / total_batches * 100) if total_batches > 0 else 0
        
        print(f"\n🎯 Batch Processing Session Summary")
        print(f"{'='*50}")
        print(f"⏱️  Session duration: {total_time:.1f}s")
        print(f"📊 Batches processed: {total_batches}")
        print(f"📈 Batch success rate: {success_rate:.1f}%")
        print(f"")
        print(f"🔧 Error Processing Results:")
        print(f"  • Total errors processed: {total_processed}")
        print(f"  • Errors successfully fixed: {total_fixed}")
        print(f"  • Errors that failed to fix: {total_failed}")
        print(f"  • Overall fix rate: {fix_rate:.1f}%")
        
        # Show category breakdown
        category_stats = {}
        for result in self.batch_results:
            cat = result.category
            if cat not in category_stats:
                category_stats[cat] = {'processed': 0, 'fixed': 0}
            category_stats[cat]['processed'] += result.errors_processed
            category_stats[cat]['fixed'] += result.errors_fixed
        
        if category_stats:
            print(f"\n📋 Results by Category:")
            for category, stats in category_stats.items():
                cat_fix_rate = (stats['fixed'] / stats['processed'] * 100) if stats['processed'] > 0 else 0
                print(f"  • {category.value}: {stats['fixed']}/{stats['processed']} fixed ({cat_fix_rate:.1f}%)")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if total_failed > 0:
            print(f"  • {total_failed} errors require manual review")
            print(f"  • Consider running additional focused fixes on failed errors")
        
        if fix_rate >= 80:
            print(f"  • Excellent fix rate! Most errors resolved automatically")
        elif fix_rate >= 60:
            print(f"  • Good fix rate. Some manual review recommended")
        else:
            print(f"  • Low fix rate. Manual review strongly recommended")
        
        print(f"  • Run flake8 again to verify remaining errors")
        print(f"  • Consider updating .flake8 configuration for persistent issues")
        
        # Log final summary
        self.logger.info(f"Session completed: {total_fixed}/{total_processed} errors fixed in {total_time:.1f}s")
        
        # Save detailed report to file if configured
        if self.config.get('reporting', {}).get('file_output', False):
            self._save_detailed_report()
    
    def _save_detailed_report(self):
        """Save a detailed report to file."""
        report_file = self.config.get('reporting', {}).get('output_file', 'logs/flake8_batch_summary.txt')
        
        try:
            with open(report_file, 'w') as f:
                f.write(f"Flake8 Batch Processing Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*50}\n\n")
                
                for result in self.batch_results:
                    f.write(f"Batch #{result.batch_id} - {result.category.value}\n")
                    f.write(f"  Processed: {result.errors_processed}\n")
                    f.write(f"  Fixed: {result.errors_fixed}\n")
                    f.write(f"  Failed: {result.errors_failed}\n")
                    f.write(f"  Time: {result.processing_time:.2f}s\n")
                    f.write(f"  Success: {result.success}\n")
                    f.write(f"  Files: {', '.join(result.files_modified)}\n")
                    if result.error_details:
                        f.write(f"  Errors: {'; '.join(result.error_details)}\n")
                    f.write(f"\n")
            
            print(f"📄 Detailed report saved to: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save detailed report: {e}")


class ErrorBatchProcessor:
    """Main batch processor for flake8 errors."""
    
    def __init__(self, config_path: str = "development/config/flake8_batch_config.yaml"):
        """
        Initialize the batch processor.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.categorizer = ErrorCategorizer()
        self.reporter = BatchReporter(self.config)
        
        # Processing state
        self.current_batch_id = 0
        self.total_errors_processed = 0
        self.session_start_time = None
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.reporter.logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
            return self._get_default_config()
        except Exception as e:
            self.reporter.logger.error(f"Error loading config: {e}. Using defaults.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration if file is not available."""
        return {
            'batch_processing': {
                'max_total_errors': 50,
                'default_batch_size': 10,
                'inter_batch_delay': 2,
                'max_concurrent_files': 5
            },
            'category_batch_sizes': {
                'syntax': 1,
                'undefined_vars': 3,
                'imports': 5,
                'formatting': 15,
                'style': 10,
                'docstrings': 5,
                'complexity': 2
            },
            'processing_priority': [
                'syntax', 'undefined_vars', 'imports', 
                'complexity', 'docstrings', 'style', 'formatting'
            ],
            'cline_compatibility': {
                'max_output_lines': 100,
                'pause_between_batches': True,
                'interactive_mode': True,
                'stop_on_critical_error': True
            },
            'auto_fix': {
                'safe_categories': ['formatting', 'imports'],
                'manual_categories': ['syntax', 'undefined_vars', 'complexity'],
                'create_backups': True
            },
            'reporting': {
                'console_output': True,
                'file_output': True
            },
            'logging': {
                'level': 'INFO',
                'main_log': 'logs/flake8_batch.log'
            }
        }
    
    def get_flake8_errors(self) -> List[FlakeError]:
        """
        Get current flake8 errors from the codebase.
        
        Returns:
            List of FlakeError objects
        """
        try:
            result = subprocess.run(
                ['python', '-m', 'flake8', '--config=development/config/.flake8', '.'],
                capture_output=True,
                text=True,
                cwd='.'
            )
            
            if result.returncode == 0 and not result.stdout.strip():
                print("🎉 No flake8 errors found! Codebase is clean.")
                return []
            
            return self.categorizer.parse_flake8_output(result.stdout)
            
        except Exception as e:
            self.reporter.logger.error(f"Error running flake8: {e}")
            return []
    
    def process_errors_in_batches(self, dry_run: bool = False) -> bool:
        """
        Process all flake8 errors in manageable batches.
        
        Args:
            dry_run: If True, only simulate processing without making changes
            
        Returns:
            True if processing completed successfully
        """
        self.session_start_time = datetime.now()
        
        # Get all current errors
        all_errors = self.get_flake8_errors()
        
        if not all_errors:
            return True
        
        # Check if we exceed maximum error threshold
        max_errors = self.config['batch_processing']['max_total_errors']
        if len(all_errors) > max_errors:
            print(f"⚠️  Found {len(all_errors)} errors, exceeding maximum of {max_errors}")
            print(f"   This could cause interface overload. Consider:")
            print(f"   1. Increasing max_total_errors in config")
            print(f"   2. Running on a subset of files")
            print(f"   3. Processing specific error categories only")
            return False
        
        # Categorize and prioritize errors
        categorized = self.categorizer.categorize_errors(all_errors)
        category_counts = {cat: len(errors) for cat, errors in categorized.items()}
        
        # Report session start
        self.reporter.report_session_start(len(all_errors), category_counts)
        
        # Process categories in priority order
        priority_order = self.config['processing_priority']
        overall_success = True
        
        for category_name in priority_order:
            category = ErrorCategory(category_name)
            
            if category not in categorized:
                continue
            
            errors_in_category = categorized[category]
            success = self._process_category_batches(category, errors_in_category, dry_run)
            
            if not success:
                overall_success = False
                
                # Check if we should stop on critical errors
                if (category in [ErrorCategory.SYNTAX, ErrorCategory.UNDEFINED_VARS] and 
                    self.config['cline_compatibility']['stop_on_critical_error']):
                    print(f"⛔ Stopping due to critical errors in {category.value}")
                    break
        
        # Report final summary
        self.reporter.report_session_summary()
        
        return overall_success
    
    def _process_category_batches(self, category: ErrorCategory, errors: List[FlakeError], dry_run: bool = False) -> bool:
        """
        Process all errors in a category using batches.
        
        Args:
            category: Error category to process
            errors: List of errors in this category
            dry_run: If True, only simulate processing
            
        Returns:
            True if category processing completed successfully
        """
        if not errors:
            return True
        
        # Get batch size for this category
        batch_sizes = self.config.get('category_batch_sizes', {})
        batch_size = batch_sizes.get(category.value, self.config['batch_processing']['default_batch_size'])
        
        # Split errors into batches
        batches = self._create_batches(errors, batch_size)
        category_success = True
        
        print(f"\n📦 Processing {len(errors)} {category.value} errors in {len(batches)} batches")
        
        for i, batch in enumerate(batches):
            self.current_batch_id += 1
            
            # Process this batch
            batch_success = self._process_single_batch(
                self.current_batch_id, category, batch, dry_run
            )
            
            if not batch_success:
                category_success = False
                
                # Check if we should continue with remaining batches
                if category in [ErrorCategory.SYNTAX, ErrorCategory.UNDEFINED_VARS]:
                    print(f"⚠️  Critical error in batch. Continuing with remaining {category.value} batches...")
            
            # Inter-batch delay for Cline compatibility
            if i < len(batches) - 1:  # Don't delay after last batch
                delay = self.config['batch_processing']['inter_batch_delay']
                if delay > 0:
                    print(f"⏳ Waiting {delay}s before next batch...")
                    time.sleep(delay)
                
                # Interactive pause for Cline compatibility
                if self.config['cline_compatibility']['pause_between_batches']:
                    input(f"⏸️  Press Enter to continue to next batch ({i+2}/{len(batches)})...")
        
        return category_success
    
    def _create_batches(self, errors: List[FlakeError], batch_size: int) -> List[List[FlakeError]]:
        """
        Split errors into batches of specified size.
        
        Args:
            errors: List of errors to batch
            batch_size: Maximum errors per batch
            
        Returns:
            List of error batches
        """
        batches = []
        for i in range(0, len(errors), batch_size):
            batch = errors[i:i + batch_size]
            batches.append(batch)
        return batches
    
    def _process_single_batch(self, batch_id: int, category: ErrorCategory, errors: List[FlakeError], dry_run: bool = False) -> bool:
        """
        Process a single batch of errors.
        
        Args:
            batch_id: Batch identifier
            category: Error category
            errors: List of errors in this batch
            dry_run: If True, only simulate processing
            
        Returns:
            True if batch processing succeeded
        """
        start_time = time.time()
        self.reporter.report_batch_start(batch_id, category, errors)
        
        errors_fixed = 0
        errors_failed = 0
        files_modified = []
        error_details = []
        
        # Group errors by file to optimize processing
        errors_by_file = {}
        for error in errors:
            if error.file_path not in errors_by_file:
                errors_by_file[error.file_path] = []
            errors_by_file[error.file_path].append(error)
        
        # Process each file
        for i, (file_path, file_errors) in enumerate(errors_by_file.items()):
            self.reporter.report_batch_progress(batch_id, i + 1, len(errors_by_file), file_path)
            
            try:
                if dry_run:
                    # Simulate processing
                    fixed_count = len(file_errors)  # Assume all would be fixed in dry run
                    files_modified.append(file_path)
                else:
                    # Actually process the file
                    fixed_count = self._fix_errors_in_file(file_path, file_errors, category)
                    if fixed_count > 0:
                        files_modified.append(file_path)
                
                errors_fixed += fixed_count
                errors_failed += len(file_errors) - fixed_count
                
            except Exception as e:
                error_msg = f"Failed to process {file_path}: {str(e)}"
                error_details.append(error_msg)
                errors_failed += len(file_errors)
                self.reporter.logger.error(error_msg)
        
        # Create batch result
        processing_time = time.time() - start_time
        result = BatchResult(
            batch_id=batch_id,
            category=category,
            errors_processed=len(errors),
            errors_fixed=errors_fixed,
            errors_failed=errors_failed,
            files_modified=files_modified,
            processing_time=processing_time,
            success=(errors_failed == 0),
            error_details=error_details
        )
        
        self.reporter.report_batch_complete(result)
        
        return result.success
    
    def _fix_errors_in_file(self, file_path: str, errors: List[FlakeError], category: ErrorCategory) -> int:
        """
        Fix errors in a specific file.
        
        Args:
            file_path: Path to the file to fix
            errors: List of errors in this file
            category: Error category being processed
            
        Returns:
            Number of errors successfully fixed
        """
        # Check if this category can be automatically fixed
        safe_categories = self.config['auto_fix']['safe_categories']
        
        if category.value not in safe_categories:
            # Manual review required
            print(f"⚠️  {file_path}: {len(errors)} {category.value} errors require manual review")
            return 0
        
        # For now, implement basic fixes for safe categories
        fixed_count = 0
        
        try:
            if category == ErrorCategory.FORMATTING:
                fixed_count = self._fix_formatting_errors(file_path, errors)
            elif category == ErrorCategory.IMPORTS:
                fixed_count = self._fix_import_errors(file_path, errors)
            else:
                # Other categories - placeholder for future implementation
                print(f"ℹ️  {file_path}: {category.value} fixes not yet implemented")
                
        except Exception as e:
            self.reporter.logger.error(f"Error fixing {file_path}: {e}")
            return 0
        
        return fixed_count
    
    def _fix_formatting_errors(self, file_path: str, errors: List[FlakeError]) -> int:
        """
        Fix formatting errors in a file.
        
        Args:
            file_path: Path to the file
            errors: List of formatting errors
            
        Returns:
            Number of errors fixed
        """
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Track which lines we've modified
            modified_lines = set()
            fixed_count = 0
            
            # Sort errors by line number (reverse order to avoid line number shifts)
            sorted_errors = sorted(errors, key=lambda e: e.line_number, reverse=True)
            
            for error in sorted_errors:
                line_idx = error.line_number - 1  # Convert to 0-based index
                
                if line_idx >= len(lines):
                    continue
                
                line = lines[line_idx]
                original_line = line
                
                # Fix specific formatting issues
                if error.error_code == 'W291':  # trailing whitespace
                    line = line.rstrip() + '\n'
                elif error.error_code == 'W293':  # blank line contains whitespace
                    if line.strip() == '':
                        line = '\n'
                elif error.error_code == 'W292':  # no newline at end of file
                    if line_idx == len(lines) - 1 and not line.endswith('\n'):
                        line = line + '\n'
                
                # Update line if it was modified
                if line != original_line:
                    lines[line_idx] = line
                    modified_lines.add(line_idx)
                    fixed_count += 1
            
            # Write back the file if we made changes
            if modified_lines:
                with open(file_path, 'w') as f:
                    f.writelines(lines)
                
                print(f"✅ Fixed {fixed_count} formatting errors in {file_path}")
            
            return fixed_count
            
        except Exception as e:
            self.reporter.logger.error(f"Error fixing formatting in {file_path}: {e}")
            return 0
    
    def _fix_import_errors(self, file_path: str, errors: List[FlakeError]) -> int:
        """
        Fix import errors in a file.
        
        Args:
            file_path: Path to the file
            errors: List of import errors
            
        Returns:
            Number of errors fixed
        """
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            fixed_count = 0
            lines_to_remove = set()
            
            for error in errors:
                if error.error_code == 'F401':  # unused import
                    line_idx = error.line_number - 1
                    if line_idx < len(lines):
                        line = lines[line_idx].strip()
                        # Simple check for import statements we can safely remove
                        if line.startswith('import ') or line.startswith('from '):
                            lines_to_remove.add(line_idx)
                            fixed_count += 1
            
            # Remove the unused import lines
            if lines_to_remove:
                # Remove lines in reverse order to maintain indices
                for line_idx in sorted(lines_to_remove, reverse=True):
                    del lines[line_idx]
                
                with open(file_path, 'w') as f:
                    f.writelines(lines)
                
                print(f"✅ Removed {fixed_count} unused imports from {file_path}")
            
            return fixed_count
            
        except Exception as e:
            self.reporter.logger.error(f"Error fixing imports in {file_path}: {e}")
            return 0


def main():
    """Main entry point for the batch processor."""
    processor = ErrorBatchProcessor()
    
    print("� Flake8 Batch Error Processor")
    print("================================")
    print("Preventing Cline interface overload through incremental processing\n")
    
    # Run in dry-run mode first to preview
    print("🔍 Running preview mode to analyze errors...")
    success = processor.process_errors_in_batches(dry_run=True)
    
    if success:
        print("✅ Preview completed successfully!")
    else:
        print("❌ Preview identified issues that need attention.")


if __name__ == "__main__":
    main()
