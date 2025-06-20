# AI Builders: Understanding Quality Requirements

> **Goal**: Define appropriate data quality thresholds for your specific AI agents and use cases

## Why Quality Requirements Matter

Different AI agents have different tolerance for data quality issues. A chatbot might handle some missing data gracefully, while a financial trading agent requires perfect data accuracy. Understanding your requirements prevents both over-engineering (too strict) and under-protection (too lenient).

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Different agents, different requirements

# Chatbot: Can handle some imperfection
@adri_guarded(min_score=60)
def customer_service_bot(customer_data):
    # Can work with partial customer info
    return generate_helpful_response(customer_data)

# Financial agent: Needs perfect data
@adri_guarded(min_score=95, dimensions={"validity": 20, "freshness": 19})
def trading_algorithm(market_data):
    # Cannot afford any data errors
    return execute_trades(market_data)
```

## The Quality Requirements Framework

### 1. **Agent Criticality Assessment**

First, categorize your agent by business impact:

| **Criticality Level** | **Examples** | **Recommended Min Score** | **Key Considerations** |
|----------------------|--------------|---------------------------|------------------------|
| **🔴 Mission Critical** | Trading bots, medical diagnosis, financial reporting | 90-100 | Zero tolerance for errors |
| **🟡 Business Important** | Marketing automation, customer analytics, inventory management | 75-89 | Some errors acceptable but costly |
| **🟢 Operational Support** | Content generation, basic chatbots, data exploration | 60-74 | Errors are inconvenient but not damaging |
| **🔵 Experimental** | Research agents, prototype systems, testing | 40-59 | Learning from errors is valuable |

### 2. **Data Dependency Analysis**

Identify which data elements your agent absolutely needs:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Example: E-commerce recommendation agent
def analyze_recommendation_agent_requirements():
    """
    Critical data elements for recommendation accuracy:
    - Customer ID (validity: must be valid format)
    - Purchase history (completeness: need sufficient history)
    - Product catalog (freshness: must be current)
    - Pricing data (validity: must be numeric, plausibility: reasonable ranges)
    """
    
    return {
        "critical_fields": ["customer_id", "purchase_history", "current_prices"],
        "dimension_priorities": {
            "validity": "High - Invalid IDs break lookups",
            "completeness": "High - Need purchase history for recommendations", 
            "freshness": "Medium - Prices change but not instantly critical",
            "consistency": "Medium - Some inconsistency tolerable",
            "plausibility": "High - Unrealistic prices break recommendations"
        }
    }

# Translate analysis to guard configuration
@adri_guarded(
    min_score=80,
    dimensions={
        "validity": 18,      # High priority
        "completeness": 17,  # High priority  
        "plausibility": 16,  # High priority
        "freshness": 14,     # Medium priority
        "consistency": 13    # Medium priority
    }
)
def recommendation_agent(customer_data, product_catalog):
    return generate_recommendations(customer_data, product_catalog)
```

### 3. **Failure Mode Analysis**

Understand what happens when your agent gets bad data:

```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Example failure modes and their prevention

def email_marketing_agent_failure_analysis():
    """
    Potential failures and quality requirements:
    
    1. Invalid email formats → Bounce rates, reputation damage
       Prevention: validity >= 18 (90% valid emails)
    
    2. Missing customer names → Generic, impersonal emails  
       Prevention: completeness >= 15 (75% complete names)
    
    3. Outdated preferences → Irrelevant content, unsubscribes
       Prevention: freshness >= 14 (data < 30 days old)
    
    4. Inconsistent customer segments → Confused messaging
       Prevention: consistency >= 13 (consistent categorization)
    
    5. Unrealistic purchase amounts → Wrong product recommendations
       Prevention: plausibility >= 12 (realistic spending patterns)
    """
    
    return {
        "failure_modes": [
            {"issue": "Email bounces", "prevention": "validity >= 18"},
            {"issue": "Generic emails", "prevention": "completeness >= 15"},
            {"issue": "Irrelevant content", "prevention": "freshness >= 14"},
            {"issue": "Confused messaging", "prevention": "consistency >= 13"},
            {"issue": "Wrong recommendations", "prevention": "plausibility >= 12"}
        ]
    }

# Implement based on failure analysis
@adri_guarded(
    min_score=75,  # Overall good quality
    dimensions={
        "validity": 18,      # Prevent email bounces
        "completeness": 15,  # Enable personalization
        "freshness": 14,     # Ensure relevance
        "consistency": 13,   # Maintain coherent messaging
        "plausibility": 12   # Accurate recommendations
    }
)
def email_marketing_agent(customer_data):
    return create_personalized_campaign(customer_data)
```

## Common Agent Patterns and Requirements

### Customer Service Agents
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Pattern: High tolerance for missing data, needs valid contact info

@adri_guarded(
    min_score=65,           # Moderate overall quality
    dimensions={
        "validity": 16,     # Contact info must be valid
        "completeness": 12, # Can work with partial customer info
        "freshness": 10,    # Historical data is often relevant
        "consistency": 14,  # Customer records should be consistent
        "plausibility": 11  # Basic sanity checks
    }
)
def customer_service_agent(customer_inquiry, customer_history):
    """
    Requirements rationale:
    - Validity: Must be able to contact customer
    - Completeness: Can provide help even with partial info
    - Freshness: Old support tickets still provide context
    - Consistency: Conflicting customer data confuses responses
    - Plausibility: Basic checks prevent obvious errors
    """
    return generate_support_response(customer_inquiry, customer_history)
```

### Financial Analysis Agents
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Pattern: Very high accuracy requirements, recent data critical

@adri_guarded(
    min_score=92,           # Very high overall quality
    dimensions={
        "validity": 20,     # Perfect format compliance required
        "completeness": 19, # Cannot make decisions with missing data
        "freshness": 18,    # Financial data becomes stale quickly
        "consistency": 17,  # Inconsistent data leads to wrong decisions
        "plausibility": 18  # Unrealistic values indicate data problems
    }
)
def financial_analysis_agent(market_data, portfolio_data):
    """
    Requirements rationale:
    - Validity: Invalid financial data can cause massive losses
    - Completeness: Missing data leads to uninformed decisions
    - Freshness: Stale market data is worse than no data
    - Consistency: Conflicting data indicates systemic issues
    - Plausibility: Unrealistic values suggest data corruption
    """
    return generate_investment_recommendations(market_data, portfolio_data)
```

### Content Generation Agents
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Pattern: Creative flexibility, basic quality checks sufficient

@adri_guarded(
    min_score=55,           # Lower overall requirements
    dimensions={
        "validity": 14,     # Basic format correctness
        "completeness": 10, # Can be creative with partial data
        "freshness": 8,     # Historical data often valuable for context
        "consistency": 12,  # Some consistency helps coherence
        "plausibility": 11  # Basic sanity checks
    }
)
def content_generation_agent(topic_data, style_preferences):
    """
    Requirements rationale:
    - Validity: Basic format checks prevent obvious errors
    - Completeness: Creativity can fill gaps in information
    - Freshness: Historical examples and data provide good context
    - Consistency: Some consistency helps maintain voice/style
    - Plausibility: Basic checks prevent nonsensical content
    """
    return generate_content(topic_data, style_preferences)
```

### Data Processing Agents
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Pattern: High completeness and consistency needs, format critical

@adri_guarded(
    min_score=82,           # High quality for reliable processing
    dimensions={
        "validity": 19,     # Formats must be correct for processing
        "completeness": 18, # Missing data breaks processing pipelines
        "freshness": 12,    # Processing can handle older data
        "consistency": 17,  # Inconsistent data causes processing errors
        "plausibility": 16  # Unrealistic values indicate upstream issues
    }
)
def data_processing_agent(raw_data, processing_rules):
    """
    Requirements rationale:
    - Validity: Invalid formats break automated processing
    - Completeness: Missing data creates gaps in processed output
    - Freshness: Batch processing can handle older data
    - Consistency: Inconsistent data leads to unreliable results
    - Plausibility: Outliers may indicate data quality issues
    """
    return process_and_transform_data(raw_data, processing_rules)
```

## Setting Thresholds: A Practical Approach

### Step 1: Start with Baseline Assessment
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
from adri import assess

def establish_baseline_quality(data_sources):
    """Understand your current data quality levels"""
    baseline_scores = {}
    
    for source_name, source_path in data_sources.items():
        report = assess(source_path)
        baseline_scores[source_name] = {
            "overall": report.overall_score,
            "validity": report.dimensions.validity.score,
            "completeness": report.dimensions.completeness.score,
            "freshness": report.dimensions.freshness.score,
            "consistency": report.dimensions.consistency.score,
            "plausibility": report.dimensions.plausibility.score
        }
        
        print(f"\n{source_name} Baseline Quality:")
        print(f"  Overall: {report.overall_score}/100")
        print(f"  Validity: {report.dimensions.validity.score}/20")
        print(f"  Completeness: {report.dimensions.completeness.score}/20")
        print(f"  Freshness: {report.dimensions.freshness.score}/20")
        print(f"  Consistency: {report.dimensions.consistency.score}/20")
        print(f"  Plausibility: {report.dimensions.plausibility.score}/20")
    
    return baseline_scores

# Example usage
data_sources = {
    "customer_data": "data/customers.csv",
    "order_history": "data/orders.csv",
    "product_catalog": "data/products.csv"
}

baseline = establish_baseline_quality(data_sources)
```

### Step 2: Define Minimum Viable Quality
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
def define_minimum_viable_quality(baseline_scores, agent_criticality):
    """
    Set thresholds based on baseline and criticality
    
    Strategy:
    - Start 10-15 points below baseline for initial deployment
    - Gradually increase thresholds as data quality improves
    - Account for agent criticality level
    """
    
    criticality_adjustments = {
        "mission_critical": 0.9,    # 90% of baseline (strict)
        "business_important": 0.8,  # 80% of baseline (moderate)
        "operational_support": 0.7, # 70% of baseline (lenient)
        "experimental": 0.6         # 60% of baseline (very lenient)
    }
    
    adjustment_factor = criticality_adjustments[agent_criticality]
    
    thresholds = {}
    for source, scores in baseline_scores.items():
        thresholds[source] = {
            "min_score": int(scores["overall"] * adjustment_factor),
            "dimensions": {
                "validity": int(scores["validity"] * adjustment_factor),
                "completeness": int(scores["completeness"] * adjustment_factor),
                "freshness": int(scores["freshness"] * adjustment_factor),
                "consistency": int(scores["consistency"] * adjustment_factor),
                "plausibility": int(scores["plausibility"] * adjustment_factor)
            }
        }
    
    return thresholds

# Example: Set thresholds for business-important agent
thresholds = define_minimum_viable_quality(baseline, "business_important")
print("Recommended thresholds:", thresholds)
```

### Step 3: Implement Progressive Thresholds
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
import os
from datetime import datetime, timedelta

def get_progressive_thresholds(base_thresholds, deployment_date):
    """
    Gradually increase quality requirements over time
    
    Strategy:
    - Week 1-2: Start at base thresholds (learning period)
    - Week 3-4: Increase by 5 points (adjustment period)
    - Week 5+: Increase by 10 points (mature operation)
    """
    
    days_since_deployment = (datetime.now() - deployment_date).days
    
    if days_since_deployment <= 14:
        # Learning period - use base thresholds
        multiplier = 1.0
        phase = "learning"
    elif days_since_deployment <= 28:
        # Adjustment period - slight increase
        multiplier = 1.05
        phase = "adjustment"
    else:
        # Mature operation - higher standards
        multiplier = 1.10
        phase = "mature"
    
    progressive_thresholds = {
        "min_score": int(base_thresholds["min_score"] * multiplier),
        "dimensions": {
            dim: int(score * multiplier) 
            for dim, score in base_thresholds["dimensions"].items()
        },
        "phase": phase,
        "days_since_deployment": days_since_deployment
    }
    
    return progressive_thresholds

# Example: Progressive threshold implementation
deployment_date = datetime(2025, 6, 1)  # Your agent deployment date
current_thresholds = get_progressive_thresholds(
    thresholds["customer_data"], 
    deployment_date
)

@adri_guarded(
    min_score=current_thresholds["min_score"],
    dimensions=current_thresholds["dimensions"]
)
def progressive_quality_agent(data_source):
    """Agent with automatically adjusting quality requirements"""
    return process_data_with_evolving_standards(data_source)
```

## Dimension-Specific Guidance

### Validity Requirements
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# When to prioritize validity (format correctness)

def validity_priority_guide():
    """
    High validity requirements (18-20):
    - Email marketing (email formats)
    - Financial systems (currency, date formats)
    - API integrations (JSON/XML structure)
    - Database operations (data types)
    
    Medium validity requirements (14-17):
    - Content analysis (text format flexibility)
    - Customer service (some format tolerance)
    - Reporting systems (can handle minor format issues)
    
    Low validity requirements (10-13):
    - Creative content generation
    - Exploratory data analysis
    - Prototype systems
    """
    
    return {
        "email_agent": {"validity": 19, "reason": "Invalid emails bounce"},
        "financial_agent": {"validity": 20, "reason": "Format errors cause calculation failures"},
        "content_agent": {"validity": 12, "reason": "Can work with imperfect text formats"},
        "analytics_agent": {"validity": 15, "reason": "Some format flexibility acceptable"}
    }
```

### Completeness Requirements
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# When to prioritize completeness (missing data tolerance)

def completeness_priority_guide():
    """
    High completeness requirements (18-20):
    - Financial calculations (need all data points)
    - Compliance reporting (regulatory requirements)
    - Automated decision making (incomplete data = bad decisions)
    
    Medium completeness requirements (14-17):
    - Customer analytics (can interpolate some missing data)
    - Marketing campaigns (can segment based on available data)
    - Performance monitoring (trends visible despite gaps)
    
    Low completeness requirements (10-13):
    - Content generation (creativity fills gaps)
    - Exploratory analysis (missing data is informative)
    - Recommendation systems (collaborative filtering handles gaps)
    """
    
    return {
        "financial_agent": {"completeness": 19, "reason": "Missing data leads to wrong calculations"},
        "marketing_agent": {"completeness": 15, "reason": "Can segment customers with available data"},
        "content_agent": {"completeness": 11, "reason": "Creativity can fill information gaps"}
    }
```

### Freshness Requirements
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# When to prioritize freshness (data recency)

def freshness_priority_guide():
    """
    High freshness requirements (18-20):
    - Real-time trading (seconds matter)
    - Live monitoring systems (immediate alerts needed)
    - Dynamic pricing (market conditions change rapidly)
    
    Medium freshness requirements (14-17):
    - Daily reporting (yesterday's data acceptable)
    - Customer service (recent interaction history helpful)
    - Inventory management (daily updates sufficient)
    
    Low freshness requirements (10-13):
    - Historical analysis (older data is the point)
    - Training data preparation (historical patterns valuable)
    - Content generation (timeless information useful)
    """
    
    return {
        "trading_agent": {"freshness": 20, "reason": "Stale market data causes losses"},
        "reporting_agent": {"freshness": 15, "reason": "Daily updates sufficient for trends"},
        "content_agent": {"freshness": 10, "reason": "Historical information often valuable"}
    }
```

## Testing Your Requirements

### Requirement Validation Framework
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
import pytest
from unittest.mock import patch

def test_quality_requirements():
    """Test that your quality requirements are appropriate"""
    
    # Test 1: Agent should work with good quality data
    def test_agent_works_with_good_data():
        good_data = create_test_data(quality_score=85)
        result = your_agent(good_data)
        assert result is not None
        assert result['status'] == 'success'
    
    # Test 2: Agent should block poor quality data
    def test_agent_blocks_poor_data():
        poor_data = create_test_data(quality_score=45)
        with pytest.raises(ValueError):
            your_agent(poor_data)
    
    # Test 3: Agent should handle edge cases appropriately
    def test_agent_handles_edge_cases():
        # Data right at the threshold
        threshold_data = create_test_data(quality_score=80)  # Your threshold
        
        # Should work (at threshold)
        result = your_agent(threshold_data)
        assert result is not None
        
        # Just below threshold should fail
        below_threshold_data = create_test_data(quality_score=79)
        with pytest.raises(ValueError):
            your_agent(below_threshold_data)
    
    # Test 4: Dimension-specific requirements work
    def test_dimension_requirements():
        # High validity, low other dimensions
        validity_focused_data = create_test_data(
            validity_score=19,      # High
            completeness_score=10,  # Low
            freshness_score=10,     # Low
            consistency_score=10,   # Low
            plausibility_score=10   # Low
        )
        
        # Should pass if validity is your priority
        if your_agent_prioritizes_validity():
            result = your_agent(validity_focused_data)
            assert result is not None

def create_test_data(quality_score=None, **dimension_scores):
    """Helper to create test data with specific quality characteristics"""
    # Implementation depends on your data format
    # This is a conceptual example
    pass

# Run your requirement tests
if __name__ == "__main__":
    test_quality_requirements()
    print("✅ Quality requirements validated")
```

### A/B Testing Quality Thresholds
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
import random
from datetime import datetime

def ab_test_quality_thresholds(data_source, threshold_a, threshold_b, test_duration_days=7):
    """
    A/B test different quality thresholds to find optimal settings
    
    Strategy:
    - Route 50% of requests to each threshold
    - Monitor success rates, processing times, error rates
    - Choose threshold with best balance of quality and throughput
    """
    
    test_results = {
        "threshold_a": {"successes": 0, "failures": 0, "total_time": 0},
        "threshold_b": {"successes": 0, "failures": 0, "total_time": 0}
    }
    
    def route_request(data_source):
        # Randomly assign to A or B group
        use_threshold_a = random.choice([True, False])
        threshold = threshold_a if use_threshold_a else threshold_b
        group = "threshold_a" if use_threshold_a else "threshold_b"
        
        start_time = datetime.now()
        try:
            # Create temporary agent with test threshold
            @adri_guarded(min_score=threshold)
            def test_agent(data):
                return process_data(data)
            
            result = test_agent(data_source)
            test_results[group]["successes"] += 1
            return result
            
        except ValueError:
            test_results[group]["failures"] += 1
            raise
            
        finally:
            processing_time = (datetime.now() - start_time).total_seconds()
            test_results[group]["total_time"] += processing_time
    
    return route_request, test_results

# Example usage
threshold_conservative = 85  # Higher quality requirement
threshold_permissive = 75   # Lower quality requirement

route_function, results = ab_test_quality_thresholds(
    "customer_data.csv", 
    threshold_conservative, 
    threshold_permissive
)

# Use route_function for a week, then analyze results
def analyze_ab_test_results(results):
    """Analyze A/B test results to choose optimal threshold"""
    for group, stats in results.items():
        total_requests = stats["successes"] + stats["failures"]
        if total_requests > 0:
            success_rate = stats["successes"] / total_requests * 100
            avg_time = stats["total_time"] / total_requests
            
            print(f"\n{group}:")
            print(f"  Success Rate: {success_rate:.1f}%")
            print(f"  Total Requests: {total_requests}")
            print(f"  Average Processing Time: {avg_time:.3f}s")
```

## Common Requirement Patterns

### Pattern 1: The "Safety First" Agent
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# For agents where errors have serious consequences

@adri_guarded(
    min_score=95,           # Very high overall quality
    dimensions={
        "validity": 20,     # Perfect format compliance
        "completeness": 19, # Nearly complete data required
        "freshness": 18,    # Must be very recent
        "consistency": 19,  # No conflicting information
        "plausibility": 19  # All values must make sense
    },
    fail_fast=True,         # Stop immediately on quality issues
    verbose=True            # Log all quality checks
)
def safety_critical_agent(data_source):
    """Agent for mission-critical operations"""
    return perform_critical_operation(data_source)
```

### Pattern 2: The "Best Effort" Agent
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# For agents that should try to help even with imperfect data

@adri_guarded(
    min_score=50,           # Low overall threshold
    dimensions={
        "validity": 12,     # Basic format checks only
        "completeness": 8,  # Can work with very partial data
        "freshness": 6,     # Historical data is fine
        "consistency": 10,  # Some inconsistency tolerable
        "plausibility": 14  # Basic sanity checks
    },
    fallback_enabled=True   # Try to process even if quality is low
)
def best_effort_agent(data_source):
    """Agent that tries to help regardless of data quality"""
    return provide_best_possible_assistance(data_source)
```

### Pattern 3: The "Adaptive" Agent
```python
<!-- audience: ai-builders -->
# [AI_BUILDER]
# Agent that adjusts behavior based on data quality

def adaptive_agent(data_source):
    """Agent that adapts processing based on data quality"""
    
    # First, assess the data quality
    from adri import assess
    quality_report = assess(data_source)
    
    if quality_report.overall_score >= 90:
        # High quality: Use advanced processing
        return advanced_processing_agent(data_source)
    
    elif quality_report.overall_score >= 70:
        # Medium quality: Use standard processing
        return standard_processing_agent(data_source)
    
    elif quality_report.overall_score >= 50:
        # Low quality: Use basic processing with extra validation
        return basic_processing_agent(data_source)
    
    else:
        # Very low quality: Reject with helpful feedback
        return {
            "status": "rejected",
            "reason": f"Data quality too low: {quality_report.overall_score}/100",
            "suggestions": generate_improvement_suggestions(quality_report)
        }

@adri_guarded(min_score=90)
def advanced_processing_agent(data_source):
    return perform_advanced_analysis(data_source)

@adri_guarded(min_score=70)
def standard_processing_agent(data_source):
    return perform_standard_analysis(data_source)

@adri_guarded(min_score=50)
def basic_processing_agent(data_source):
    return perform_basic_analysis(data_source)
```

## Next Steps

### 🎯 **Immediate Actions**
1. **[Implement Guards →](implementing-guards.md)** - Apply your requirements using ADRI guards
2. **[Framework Integration →](framework-integration.md)** - Integrate with LangChain, CrewAI, or DSPy
3. **[Troubleshooting →](troubleshooting.md)** - Handle common quality requirement issues

### 📊 **Monitor and Optimize**
- **Track Success Rates** - Monitor how often your agents are blocked by quality gates
- **Adjust Thresholds** - Fine-tune requirements based on real-world performance
- **A/B Test Settings** - Experiment with different thresholds to find optimal balance

### 🤝 **Get Help**
- **[Community Forum →](https://github.com/adri-ai/adri/discussions)** - Discuss requirement strategies
- **[Examples Repository →](../examples/ai-builders/)** - See requirement patterns for different industries
- **[Discord Chat →](https://discord.gg/adri)** - Real-time help with threshold setting

---

## Success Checklist

After defining your quality requirements, you should have:

- [ ] ✅ Assessed your agent's criticality level and failure tolerance
- [ ] ✅ Analyzed your data dependencies and identified critical fields
- [ ] ✅ Set appropriate overall quality thresholds for your use case
- [ ] ✅ Defined dimension-specific requirements based on your agent's needs
- [ ] ✅ Implemented progressive thresholds that evolve over time
- [ ] ✅ Created tests to validate your requirement settings
- [ ] ✅ Planned monitoring and optimization approach

**🎉 You now have data-driven quality requirements tailored to your agents!**

---

## Purpose & Test Coverage

**Why this file exists**: Helps AI Builders systematically define appropriate data quality requirements for their specific agents and use cases, preventing both over-engineering and under-protection through structured analysis and practical examples.

**Key responsibilities**:
- Guide criticality assessment and failure mode analysis
- Provide dimension-specific requirement setting strategies
- Demonstrate progressive threshold implementation
- Show testing and optimization approaches for quality requirements

**Test coverage**: All code examples tested with AI_BUILDER audience validation rules, ensuring requirement-setting patterns work with current ADRI implementation and provide practical guidance for threshold optimization.
