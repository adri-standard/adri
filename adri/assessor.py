"""
Core assessment logic for the Agent Data Readiness Index.

This module provides the main DataSourceAssessor class that coordinates
the assessment of data sources across all dimensions.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .dimensions import (
    ValidityAssessor,
    CompletenessAssessor,
    FreshnessAssessor,
    ConsistencyAssessor,
    PlausibilityAssessor,
)
from .connectors import (
    BaseConnector,
    FileConnector,
    DatabaseConnector,
    APIConnector,
)
from .report import AssessmentReport
from .utils.validators import validate_config

logger = logging.getLogger(__name__)


class DataSourceAssessor:
    """
    Main assessor class for evaluating data sources against the
    Agent Data Readiness Index criteria.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the assessor with optional custom configuration.

        Args:
            config: Optional configuration dictionary that can customize
                   dimension weights, thresholds, etc.
        """
        self.config = config or {}
        validate_config(self.config)

        # Initialize dimension assessors
        self.dimensions = {
            "validity": ValidityAssessor(self.config.get("validity", {})),
            "completeness": CompletenessAssessor(self.config.get("completeness", {})),
            "freshness": FreshnessAssessor(self.config.get("freshness", {})),
            "consistency": ConsistencyAssessor(self.config.get("consistency", {})),
            "plausibility": PlausibilityAssessor(self.config.get("plausibility", {})),
        }

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
        connector = FileConnector(file_path, file_type)
        return self.assess_source(connector)

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
        connector = DatabaseConnector(connection_string, table_name)
        return self.assess_source(connector)

    def assess_api(self, endpoint: str, auth: Optional[Dict[str, Any]] = None) -> AssessmentReport:
        """
        Assess an API endpoint.

        Args:
            endpoint: API endpoint URL
            auth: Optional authentication details

        Returns:
            AssessmentReport: The assessment results
        """
        connector = APIConnector(endpoint, auth)
        return self.assess_source(connector)

    def assess_source(self, connector: BaseConnector) -> AssessmentReport:
        """
        Assess any data source using a connector.

        Args:
            connector: Data source connector instance

        Returns:
            AssessmentReport: The assessment results
        """
        logger.info(f"Starting assessment of {connector}")
        
        # Initialize report
        report = AssessmentReport(
            source_name=connector.get_name(),
            source_type=connector.get_type(),
            source_metadata=connector.get_metadata(),
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
