"""
Example demonstrating ADRI template-based assessment.

This example shows how to use certification templates to standardize
data quality requirements across teams and organizations.
"""

import logging
from pathlib import Path

from adri.assessor import DataSourceAssessor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_sample_dataset_path():
    """Get the path to a sample dataset for demonstration."""
    example_dir = Path(__file__).parent
    sample_path = example_dir / "plausibility" / "sample_dataset.csv"
    
    # If the sample dataset doesn't exist, use a test dataset
    if not sample_path.exists():
        repo_root = Path(__file__).parent.parent
        sample_path = repo_root / "tests" / "datasets" / "ideal_dataset.csv"
        
    if not sample_path.exists():
        raise FileNotFoundError("Could not find a sample dataset for the example.")
        
    return str(sample_path)


def assess_with_production_template():
    """Demonstrate assessment using the production template."""
    logger.info("=== TEMPLATE-BASED ASSESSMENT EXAMPLE ===")
    
    # Get sample data
    data_path = get_sample_dataset_path()
    logger.info(f"Using sample dataset: {data_path}")
    
    # Create assessor
    assessor = DataSourceAssessor()
    
    # Assess with the production template
    logger.info("\nAssessing data against Production v1.0.0 template...")
    # Get path to the template file
    template_path = Path(__file__).parent.parent / "adri" / "templates" / "catalog" / "general" / "production-v1.0.0.yaml"
    report, evaluation = assessor.assess_file_with_template(
        file_path=data_path,
        template_source=str(template_path)  # Use file path directly
    )
    
    # Display basic assessment results
    logger.info(f"\nBasic Assessment Results:")
    logger.info(f"Overall Score: {report.overall_score}/100")
    logger.info(f"Readiness Level: {report.readiness_level}")
    
    # Display template evaluation results
    logger.info(f"\nTemplate Evaluation Results:")
    logger.info(f"Template: {evaluation.template_id}")
    logger.info(f"Compliant: {evaluation.compliant}")
    logger.info(f"Compliance Score: {evaluation.compliance_score:.1f}%")
    logger.info(f"Certification Eligible: {evaluation.certification_eligible}")
    
    # Show gaps if any
    if evaluation.gaps:
        logger.info(f"\nGaps Found ({len(evaluation.gaps)}):")
        for gap in evaluation.gaps[:3]:  # Show first 3 gaps
            logger.info(f"- {gap.requirement_description}")
            logger.info(f"  Required: {gap.expected_value}, Got: {gap.actual_value}")
    else:
        logger.info("\nNo gaps found - fully compliant!")
    
    # Save enhanced report
    report_path = Path(data_path).with_suffix('.template_report.html')
    report.save_html(report_path)
    logger.info(f"\nDetailed report saved to: {report_path}")
    
    return report, evaluation


def assess_with_multiple_templates():
    """Demonstrate assessment against multiple templates."""
    logger.info("\n=== MULTI-TEMPLATE ASSESSMENT ===")
    
    # Get sample data
    data_path = get_sample_dataset_path()
    
    # Create assessor
    assessor = DataSourceAssessor()
    
    # Get connector
    from adri.connectors import ConnectorRegistry
    connector_class = ConnectorRegistry.get_connector("file")
    connector = connector_class(data_path)
    
    # Assess against multiple templates
    logger.info("\nAssessing against multiple templates...")
    # Get paths to template files
    repo_root = Path(__file__).parent.parent
    production_template = repo_root / "adri" / "templates" / "catalog" / "general" / "production-v1.0.0.yaml"
    basel_template = repo_root / "adri" / "templates" / "catalog" / "financial" / "basel-iii-v1.0.0.yaml"
    
    report, evaluations = assessor.assess_with_templates(
        connector=connector,
        template_sources=[
            str(production_template),
            str(basel_template)  # Financial industry template
        ]
    )
    
    # Display results for each template
    for evaluation in evaluations:
        logger.info(f"\n{evaluation.template_id}:")
        logger.info(f"  Compliance: {evaluation.compliance_score:.1f}%")
        logger.info(f"  Certification Eligible: {evaluation.certification_eligible}")
        logger.info(f"  Compliant: {evaluation.compliant}")
    
    return report, evaluations


def create_custom_template_assessment():
    """Demonstrate using a custom template file."""
    logger.info("\n=== CUSTOM TEMPLATE ASSESSMENT ===")
    
    # Create a simple custom template
    custom_template_path = Path("custom_ai_agent_template.yaml")
    custom_template_content = """# Custom AI Agent Data Requirements

template:
  id: "custom-ai-agent"
  version: "1.0.0"
  name: "AI Agent Data Quality Standard"
  authority: "Your Organization"
  description: "Custom requirements for AI agent data sources"
  effective_date: "2025-01-01"

requirements:
  # Minimum overall score for AI agents
  overall_minimum: 75
  
  # Per-dimension requirements
  dimension_requirements:
    validity:
      minimum_score: 18
      description: "Data must have proper type definitions and validation"
    
    completeness:
      minimum_score: 16
      description: "Data must be sufficiently complete"
      max_missing_percentage: 10
    
    freshness:
      minimum_score: 15
      description: "Data must be recent for AI agents"
      max_age_days: 7
    
    consistency:
      minimum_score: 16
      description: "Data must be internally consistent"
    
    plausibility:
      minimum_score: 15
      description: "Data must be plausible and free from outliers"
  
  # Recommended practices
  recommended_practices:
    - "Implement real-time validation"
    - "Monitor data quality metrics"
    - "Document data sources"

# Certification information
certification:
  badge: "🤖"
  level: "AI Agent Ready"
  validity_period_days: 90
  renewal_requirements:
    - "Maintain minimum scores"
    - "Pass quarterly audit"
"""
    
    # Write the custom template
    with open(custom_template_path, 'w') as f:
        f.write(custom_template_content)
    
    logger.info(f"Created custom template: {custom_template_path}")
    
    try:
        # Get sample data
        data_path = get_sample_dataset_path()
        
        # Create assessor
        assessor = DataSourceAssessor()
        
        # Assess with custom template
        report, evaluation = assessor.assess_file_with_template(
            file_path=data_path,
            template_source=str(custom_template_path)
        )
        
        logger.info(f"\nCustom Template Results:")
        logger.info(f"Template: {evaluation.template_id}")
        logger.info(f"Compliance: {evaluation.compliance_score:.1f}%")
        logger.info(f"Certification Eligible: {evaluation.certification_eligible}")
        
    finally:
        # Clean up
        if custom_template_path.exists():
            custom_template_path.unlink()
            logger.info(f"Cleaned up custom template file")


def main():
    """Run all template assessment examples."""
    try:
        # Basic template assessment
        assess_with_production_template()
        
        # Multiple templates
        assess_with_multiple_templates()
        
        # Custom template
        create_custom_template_assessment()
        
        logger.info("\n=== TEMPLATE ASSESSMENT COMPLETE ===")
        logger.info("Templates enable:")
        logger.info("- Standardized quality requirements across teams")
        logger.info("- Clear certification levels")
        logger.info("- Gap analysis for improvement")
        logger.info("- Industry-specific standards")
        
    except Exception as e:
        logger.error(f"Error in demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
