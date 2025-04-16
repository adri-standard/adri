"""
Core assessment logic for the Agent Data Readiness Index.

This module provides the main DataSourceAssessor class that coordinates
the assessment of data sources across all dimensions.
"""

import logging
import importlib.metadata
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Type

from .dimensions import BaseDimensionAssessor, DimensionRegistry
from .connectors import BaseConnector, ConnectorRegistry
from .report import AssessmentReport
from .utils.validators import validate_config

logger = logging.getLogger(__name__)


class DataSourceAssessor:
    """
    Main assessor class for evaluating data sources against the
    Agent Data Readiness Index criteria.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, dimensions: Optional[List[str]] = None):
        """
        Initialize the assessor with optional custom configuration.

        Args:
            config: Optional configuration dictionary that can customize
                   dimension weights, thresholds, etc.
            dimensions: Optional list of dimension names to use (defaults to all registered)
        """
        self.config = config or {}
        validate_config(self.config)

        # Initialize dimension assessors
        self.dimensions = {}
        dimension_names = dimensions or DimensionRegistry.list_dimensions()
        
        for name in dimension_names:
            try:
                dimension_class = DimensionRegistry.get_dimension(name)
                self.dimensions[name] = dimension_class(self.config.get(name, {}))
            except ValueError as e:
                logger.warning(f"Dimension '{name}' not found: {e}")

    def assess_with_connector(self, connector_type: str, *args, **kwargs) -> AssessmentReport:
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
        self, file_path: Union[str, Path], file_type: Optional[str] = None
    ) -> AssessmentReport:
        """
        Assess a file-based data source.

        Args:
            file_path: Path to the file to assess
            file_type: Optional file type override (csv, json, etc.)

        Returns:
            AssessmentReport: The assessment results
        """
        return self.assess_with_connector("file", file_path, file_type)

    def assess_database(
        self, connection_string: str, table_name: str
    ) -> AssessmentReport:
        """
        Assess a database table.

        Args:
            connection_string: Database connection string
            table_name: Name of the table to assess

        Returns:
            AssessmentReport: The assessment results
        """
        return self.assess_with_connector("database", connection_string, table_name)

    def assess_api(self, endpoint: str, auth: Optional[Dict[str, Any]] = None) -> AssessmentReport:
        """
        Assess an API endpoint.

        Args:
            endpoint: API endpoint URL
            auth: Optional authentication details

        Returns:
            AssessmentReport: The assessment results
        """
        return self.assess_with_connector("api", endpoint, auth)

    def assess_source(self, connector: BaseConnector) -> AssessmentReport:
        """
        Assess any data source using a connector.

        Args:
            connector: Data source connector instance

        Returns:
            AssessmentReport: The assessment results
        """
        logger.info(f"Starting assessment of {connector}")
        
        # Get ADRI version
        try:
            adri_version = importlib.metadata.version('adri')
        except importlib.metadata.PackageNotFoundError:
            adri_version = "unknown"
            logger.warning("Could not determine ADRI package version.")
            
        # Initialize report, passing version and config
        report = AssessmentReport(
            source_name=connector.get_name(),
            source_type=connector.get_type(),
            source_metadata=connector.get_metadata(),
            adri_version=adri_version,
            assessment_config=self.config, # Pass the assessor's config
        )

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
        
        logger.info(f"Assessment complete. Overall score: {report.overall_score}")
        return report

    def assess_from_config(self, config_path: Union[str, Path]) -> Dict[str, AssessmentReport]:
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
