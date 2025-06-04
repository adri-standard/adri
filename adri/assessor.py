"""
Core assessment logic for the Agent Data Readiness Index.

This module provides the main DataSourceAssessor class that coordinates
the assessment of data sources across all dimensions.
"""

import logging
import importlib.metadata
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Type, Tuple

from .dimensions import BaseDimensionAssessor, DimensionRegistry
from .connectors import BaseConnector, ConnectorRegistry
from .report import ADRIScoreReport
from .utils.validators import validate_config
from .templates import TemplateLoader, TemplateEvaluation, BaseTemplate
from .templates.guard import TemplateGuard
from .assessment_modes import AssessmentMode, ModeConfig
from .utils.metadata_generator import MetadataGenerator

logger = logging.getLogger(__name__)


class DataSourceAssessor:
    """
    Main assessor class for evaluating data sources against the
    Agent Data Readiness Index criteria.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, dimensions: Optional[List[str]] = None, 
                 mode: Union[AssessmentMode, str] = AssessmentMode.AUTO):
        """
        Initialize the assessor with optional custom configuration.

        Args:
            config: Optional configuration dictionary that can customize
                   dimension weights, thresholds, etc.
            dimensions: Optional list of dimension names to use (defaults to all registered)
            mode: Assessment mode (discovery, validation, or auto)
        """
        self.config = config or {}
        validate_config(self.config)
        
        # Set assessment mode
        if isinstance(mode, str):
            mode = AssessmentMode(mode.lower())
        self.mode = mode
        
        # Get mode-specific configuration
        self.mode_config = ModeConfig.get_mode_config(self.mode)
        
        # Merge mode config with user config (user config takes precedence)
        self.effective_config = {**self.mode_config, **self.config}

        # Initialize dimension assessors
        self.dimensions = {}
        dimension_names = dimensions or DimensionRegistry.list_dimensions()
        
        for name in dimension_names:
            try:
                dimension_class = DimensionRegistry.get_dimension(name)
                # Pass mode-aware config to dimensions
                dim_config = self.effective_config.get(name, {})
                # Ensure dimensions know about the metadata requirement and business logic setting
                dim_config['REQUIRE_EXPLICIT_METADATA'] = self.mode_config['require_explicit_metadata']
                dim_config['business_logic_enabled'] = self.mode_config.get('business_logic_enabled', False)
                self.dimensions[name] = dimension_class(dim_config)
            except ValueError as e:
                logger.warning(f"Dimension '{name}' not found: {e}")
        
        # Create safe template loader
        self._safe_load_template = TemplateGuard.create_safe_template_loader(self)

    def assess_with_connector(self, connector_type: str, *args, **kwargs) -> ADRIScoreReport:
        """
        Assess a data source using a specific connector type.
        
        Args:
            connector_type: Name of the registered connector to use
            *args, **kwargs: Arguments to pass to the connector constructor
            
        Returns:
            AssessmentReport: The assessment results
        """
        connector_class = ConnectorRegistry.get_connector(connector_type)
        connector = connector_class(*args, **kwargs)
        return self.assess_source(connector)

    def assess_file(
        self, file_path: Union[str, Path], file_type: Optional[str] = None,
        template: Optional[Union[str, BaseTemplate]] = None
    ) -> ADRIScoreReport:
        """
        Assess a file-based data source.

        Args:
            file_path: Path to the file to assess
            file_type: Optional file type override (csv, json, etc.)
            template: Optional template to use (defaults to general/default-v1.0.0)

        Returns:
            AssessmentReport: The assessment results
        """
        if template is None:
            # Use the default general template
            template_path = Path(__file__).parent / "templates" / "catalog" / "general" / "default-v1.0.0.yaml"
            template = str(template_path)
        
        # Always use template-based assessment
        report, _ = self.assess_file_with_template(file_path, template, file_type)
        return report

    def assess_database(
        self, connection_string: str, table_name: str,
        template: Optional[Union[str, BaseTemplate]] = None
    ) -> ADRIScoreReport:
        """
        Assess a database table.

        Args:
            connection_string: Database connection string
            table_name: Name of the table to assess
            template: Optional template to use (defaults to general/default-v1.0.0)

        Returns:
            AssessmentReport: The assessment results
        """
        if template is None:
            # Use the default general template
            template_path = Path(__file__).parent / "templates" / "catalog" / "general" / "default-v1.0.0.yaml"
            template = str(template_path)
        
        # Create connector and use template-based assessment
        connector_class = ConnectorRegistry.get_connector("database")
        connector = connector_class(connection_string, table_name)
        report, _ = self.assess_with_template(connector, template)
        return report

    def assess_api(
        self, endpoint: str, auth: Optional[Dict[str, Any]] = None,
        template: Optional[Union[str, BaseTemplate]] = None
    ) -> ADRIScoreReport:
        """
        Assess an API endpoint.

        Args:
            endpoint: API endpoint URL
            auth: Optional authentication details
            template: Optional template to use (defaults to general/default-v1.0.0)

        Returns:
            AssessmentReport: The assessment results
        """
        if template is None:
            # Use the default general template
            template_path = Path(__file__).parent / "templates" / "catalog" / "general" / "default-v1.0.0.yaml"
            template = str(template_path)
        
        # Create connector and use template-based assessment
        connector_class = ConnectorRegistry.get_connector("api")
        connector = connector_class(endpoint, auth)
        report, _ = self.assess_with_template(connector, template)
        return report

    def assess_source(
        self, connector: BaseConnector,
        template: Optional[Union[str, BaseTemplate]] = None
    ) -> ADRIScoreReport:
        """
        Assess any data source using a connector.

        Args:
            connector: Data source connector instance
            template: Optional template to use (defaults to general/default-v1.0.0)

        Returns:
            AssessmentReport: The assessment results
        """
        if template is None:
            # Use the default general template
            template_path = Path(__file__).parent / "templates" / "catalog" / "general" / "default-v1.0.0.yaml"
            template = str(template_path)
        
        # Always use template-based assessment
        report, _ = self.assess_with_template(connector, template)
        return report

    def _assess_source_without_template(self, connector: BaseConnector) -> ADRIScoreReport:
        """
        Internal method for assessment without template (used by assess_with_template).
        
        Args:
            connector: Data source connector instance
            
        Returns:
            AssessmentReport: The assessment results
        """
        # If mode is AUTO, detect the appropriate mode
        actual_mode = self.mode
        if self.mode == AssessmentMode.AUTO:
            # Check for metadata files
            metadata = connector.get_metadata()
            has_metadata = bool(metadata and "fields" in metadata.get("schema", {}))
            
            # Detect mode based on available information
            actual_mode = ModeConfig.detect_mode(connector, has_metadata=has_metadata)
            logger.info(f"Auto-detected assessment mode: {actual_mode.value}")
            
            # Update configuration if mode changed
            if actual_mode != AssessmentMode.AUTO:
                self.mode_config = ModeConfig.get_mode_config(actual_mode)
                # Re-initialize dimensions with new mode config
                for name, assessor in self.dimensions.items():
                    dim_config = self.effective_config.get(name, {})
                    dim_config['REQUIRE_EXPLICIT_METADATA'] = self.mode_config['require_explicit_metadata']
                    dim_config['business_logic_enabled'] = self.mode_config.get('business_logic_enabled', False)
                    self.dimensions[name] = type(assessor)(dim_config)
        
        logger.info(f"Starting assessment of {connector} in {actual_mode.value} mode")
        
        # Get ADRI version
        try:
            adri_version = importlib.metadata.version('adri')
        except importlib.metadata.PackageNotFoundError:
            adri_version = "unknown"
            logger.warning("Could not determine ADRI package version.")
            
        # Initialize report, passing version and config
        report = ADRIScoreReport(
            source_name=connector.get_name(),
            source_type=connector.get_type(),
            source_metadata=connector.get_metadata(),
            adri_version=adri_version,
            assessment_config=self.config, # Pass the assessor's config
        )
        
        # Add mode information to report
        report.assessment_mode = actual_mode.value
        report.mode_config = self.mode_config

        # Assess each dimension
        dimension_results = {}
        for dim_name, assessor in self.dimensions.items():
            logger.debug(f"Assessing {dim_name} dimension")
            score, findings, recommendations = assessor.assess(connector)
            dimension_results[dim_name] = {
                "score": score,
                "findings": findings,
                "recommendations": recommendations,
            }
            logger.debug(f"{dim_name} score: {score}")

        # Calculate overall score and populate report
        report.populate_from_dimension_results(dimension_results)
        
        # In discovery mode, generate metadata if enabled
        if actual_mode == AssessmentMode.DISCOVERY and self.mode_config.get('auto_generate_metadata', False):
            # Only generate metadata for file connectors (for now)
            if hasattr(connector, 'file_path') and hasattr(connector, 'df'):
                try:
                    logger.info("Generating ADRI metadata files...")
                    metadata_generator = MetadataGenerator(connector)
                    generated_files = metadata_generator.generate_all_metadata()
                    
                    # Add generated metadata info to report
                    report.generated_metadata = generated_files
                    report.metadata_generation_success = True
                    
                    # Add to summary findings
                    if not hasattr(report, 'summary_findings'):
                        report.summary_findings = []
                    report.summary_findings.append(
                        f"✅ Generated {len(generated_files)} metadata files to help improve data quality"
                    )
                    
                    logger.info(f"Successfully generated {len(generated_files)} metadata files")
                except Exception as e:
                    logger.warning(f"Could not generate metadata: {e}")
                    report.metadata_generation_success = False
        
        # In discovery mode, suggest templates if enabled
        if self.mode_config.get('suggest_templates', False):
            # This will be implemented in the template matcher
            report.suggested_templates = []  # Placeholder for now
        
        logger.info(f"Assessment complete. Overall score: {report.overall_score}")
        return report

    def assess_from_config(self, config_path: Union[str, Path]) -> Dict[str, ADRIScoreReport]:
        """
        Assess multiple data sources specified in a configuration file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Dict[str, AssessmentReport]: Dictionary of assessment reports
                                        keyed by source name
        """
        import yaml
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        reports = {}
        for source_config in config.get('sources', []):
            source_name = source_config.get('name', 'Unknown')
            source_type = source_config.get('type')
            
            logger.info(f"Assessing {source_name} ({source_type})")
            
            try:
                if source_type == 'file':
                    report = self.assess_file(
                        source_config['path'],
                        source_config.get('file_type')
                    )
                elif source_type == 'database':
                    report = self.assess_database(
                        source_config['connection'],
                        source_config['table']
                    )
                elif source_type == 'api':
                    report = self.assess_api(
                        source_config['endpoint'],
                        source_config.get('auth')
                    )
                else:
                    logger.error(f"Unknown source type: {source_type}")
                    continue
                    
                reports[source_name] = report
                
            except Exception as e:
                logger.error(f"Error assessing {source_name}: {e}")
                
        return reports

    def assess_with_template(
        self, 
        connector: BaseConnector,
        template_source: Union[str, BaseTemplate],
        template_version: Optional[str] = None,
        loader_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[ADRIScoreReport, TemplateEvaluation]:
        """
        Assess a data source using template rules and evaluate it against template requirements.
        
        Args:
            connector: Data source connector instance
            template_source: Template ID, file path, URL, or template instance
            template_version: Optional template version
            loader_config: Optional configuration for the template loader
            
        Returns:
            Tuple of (AssessmentReport, TemplateEvaluation)
        """
        # Load template using safe loader
        if isinstance(template_source, BaseTemplate):
            template = template_source
        else:
            if template_version and '@' not in str(template_source):
                # Add version to source if provided separately
                template_source = f"{template_source}@{template_version}"
            # Use the safe template loader
            template = self._safe_load_template(template_source, loader_config)
        
        # Configure dimensions with template rules
        template_configs = self._extract_dimension_configs_from_template(template)
        
        # Configure each dimension with template rules
        for dim_name, dim_config in template_configs.items():
            if dim_name in self.dimensions:
                self.dimensions[dim_name].set_template_rules(dim_config.get('rules', []))
                
        logger.debug(f"Configured dimensions with template '{template.template_id}' rules")
        
        # Now run assessment with template rules applied
        report = self._assess_source_without_template(connector)
        
        # Evaluate against template requirements
        evaluation = template.evaluate(report)
        
        # Add evaluation to report
        if not hasattr(report, 'template_evaluations'):
            report.template_evaluations = []
        report.template_evaluations.append(evaluation)
        
        logger.info(f"Template evaluation complete: {evaluation.get_summary()}")
        
        return report, evaluation

    def assess_file_with_template(
        self,
        file_path: Union[str, Path],
        template_source: Union[str, BaseTemplate],
        file_type: Optional[str] = None,
        template_version: Optional[str] = None
    ) -> Tuple[ADRIScoreReport, TemplateEvaluation]:
        """
        Assess a file and evaluate it against a template.
        
        Args:
            file_path: Path to the file to assess
            template_source: Template ID, file path, URL, or template instance
            file_type: Optional file type override
            template_version: Optional template version
            
        Returns:
            Tuple of (AssessmentReport, TemplateEvaluation)
        """
        connector_class = ConnectorRegistry.get_connector("file")
        connector = connector_class(file_path, file_type)
        return self.assess_with_template(connector, template_source, template_version)

    def assess_with_templates(
        self,
        connector: BaseConnector,
        template_sources: List[Union[str, BaseTemplate]],
        loader_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[ADRIScoreReport, List[TemplateEvaluation]]:
        """
        Assess a data source against multiple templates.
        
        Args:
            connector: Data source connector instance
            template_sources: List of template sources
            loader_config: Optional configuration for the template loader
            
        Returns:
            Tuple of (AssessmentReport, List[TemplateEvaluation])
        """
        # Run standard assessment once
        report = self.assess_source(connector)
        evaluations = []
        
        # Evaluate against each template
        loader = TemplateLoader(**loader_config) if loader_config else TemplateLoader()
        
        for template_source in template_sources:
            try:
                # Load template
                if isinstance(template_source, BaseTemplate):
                    template = template_source
                else:
                    template = loader.load_template(template_source)
                
                # Evaluate
                evaluation = template.evaluate(report)
                evaluations.append(evaluation)
                
                logger.info(f"Template {template.template_id}: {evaluation.get_summary()}")
                
            except Exception as e:
                logger.error(f"Error evaluating template {template_source}: {e}")
        
        # Add all evaluations to report
        if not hasattr(report, 'template_evaluations'):
            report.template_evaluations = []
        report.template_evaluations.extend(evaluations)
        
        return report, evaluations

    def _extract_dimension_configs_from_template(self, template: BaseTemplate) -> Dict[str, Dict[str, Any]]:
        """
        Extract dimension configurations from a template.
        
        Args:
            template: The template to extract configurations from
            
        Returns:
            Dict mapping dimension names to their configurations
        """
        configs = {}
        
        # Check if template has raw data (for YAML templates)
        if hasattr(template, 'template_data'):
            dimensions = template.template_data.get('dimensions', {})
            
            for dim_name, dim_config in dimensions.items():
                configs[dim_name] = {
                    'rules': dim_config.get('rules', []),
                    'weight': dim_config.get('weight', 1.0),
                    'enabled': dim_config.get('enabled', True)
                }
        
        return configs

# ----------------------------------------------
# TEST COVERAGE
# ----------------------------------------------
# This component is tested through:
# 
# 1. Unit tests:
#    - tests/unit/test_assessor.py (core assessor functionality)
# 
# 2. Integration tests:
#    - tests/integration/test_cli.py (full assessment pipeline)
#
# 3. Example usage in:
#    - examples/basic_assessment.py
#    - examples/comprehensive_assessment.py
#    - examples/consistency_assessment.py  
#    - examples/plausibility_assessment.py
#    - notebooks/01_adri_guard_tutorial.ipynb
#
# 4. Dimension coordination:
#    - Tested implicitly through all dimension tests
#    - tests/unit/dimensions/test_validity_detection.py
#    - tests/unit/dimensions/test_completeness.py
#    - tests/unit/dimensions/test_freshness_basic.py
#
# Complete test coverage details are documented in:
# docs/test_coverage/CORE_test_coverage.md
# ----------------------------------------------
