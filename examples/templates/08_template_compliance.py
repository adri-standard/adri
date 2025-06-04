#!/usr/bin/env python3
"""
Example 08: Template Compliance

This example demonstrates how to:
- Check if data meets a specific template's requirements
- Use pre-built templates (like production-v1.0.0)
- Understand compliance vs scoring
- Get actionable remediation guidance
"""

from adri import DataSourceAssessor
from adri.connectors import FileConnector
from adri.templates import TemplateRegistry

def main():
    print("=== ADRI Template Compliance Example ===\n")
    
    # Step 1: Load and assess the data
    print("1. Loading and assessing data...")
    assessor = DataSourceAssessor()
    report = assessor.assess_file("quickstart/samples/crm_data.csv")
    print(f"✓ Overall ADRI Score: {report.overall_score:.1f}/100\n")
    
    # Step 2: Load a template
    print("2. Loading production template...")
    registry = TemplateRegistry()
    template = registry.get_template("production-v1.0.0")
    
    if template:
        print(f"✓ Template: {template.template_name}")
        print(f"  Authority: {template.authority}")
        print(f"  Description: {template.description}\n")
        
        # Step 3: Check compliance
        print("3. Checking compliance...")
        evaluation = template.evaluate(report)
        
        print(f"\n{'='*50}")
        print(f"COMPLIANCE RESULT: {'✅ COMPLIANT' if evaluation.is_compliant else '❌ NON-COMPLIANT'}")
        print(f"{'='*50}\n")
        
        # Step 4: Show detailed results
        print("4. Detailed Results:")
        
        # Overall score requirement
        overall_req = evaluation.requirement_results.get('overall_score', {})
        print(f"\n📊 Overall Score Requirement:")
        print(f"   Required: {overall_req.get('required', 'N/A')}")
        print(f"   Actual: {overall_req.get('actual', 'N/A')}")
        print(f"   Status: {'✅ PASS' if overall_req.get('passed', False) else '❌ FAIL'}")
        
        # Dimension requirements
        print(f"\n📏 Dimension Requirements:")
        for dim, result in evaluation.dimension_results.items():
            req_score = result.get('required_score', 0)
            actual_score = result.get('actual_score', 0)
            passed = result.get('passed', False)
            
            status = '✅' if passed else '❌'
            print(f"   {dim.capitalize()}: {actual_score}/{req_score} {status}")
        
        # Show gaps if non-compliant
        if not evaluation.is_compliant:
            print(f"\n⚠️  Gaps to Address:")
            gaps = evaluation.get_gaps()
            
            if gaps.get('overall_gap'):
                print(f"   - Overall score needs {gaps['overall_gap']:.1f} more points")
            
            for dim, gap in gaps.get('dimension_gaps', {}).items():
                if gap > 0:
                    print(f"   - {dim.capitalize()} needs {gap:.1f} more points")
        
        # Step 5: Get remediation recommendations
        print(f"\n5. Remediation Recommendations:")
        recommendations = evaluation.get_recommendations()
        
        if recommendations:
            for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
                print(f"   {i}. {rec}")
        else:
            print("   No specific recommendations available.")
    else:
        print("❌ Could not load production template")
        print("\nAvailable templates:")
        for template_id in registry.list_templates():
            print(f"  - {template_id}")

if __name__ == "__main__":
    main()
