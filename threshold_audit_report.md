# Test Threshold Audit Report

**Total thresholds found:** 95
**Files processed:** 53

## Summary by Category

- **timing_parsing**: 40 thresholds
- **timing_processing**: 22 thresholds
- **quality_score**: 18 thresholds
- **timing_workflow**: 9 thresholds
- **benchmark_performance**: 6 thresholds

## Detailed Threshold Locations

### Timing Parsing (40 items)

**File:** `tests/integration/test_component_interactions.py:407`
**Context:** `unknown_function`
**Current:** `total_duration < 120.0`
**Suggested:** `total_duration < 600.0`
**Line:** `assert total_duration < 120.0, f"Complete pipeline too slow: {total_duration:.2f}s"`

**File:** `tests/integration/test_component_interactions.py:407`
**Context:** `unknown_function`
**Current:** `total_duration < 120.0`
**Suggested:** `total_duration < 600.0`
**Line:** `assert total_duration < 120.0, f"Complete pipeline too slow: {total_duration:.2f}s"`

**File:** `tests/integration/test_end_to_end_workflows.py:566`
**Context:** `unknown_function`
**Current:** `total_duration < 300.0`
**Suggested:** `total_duration < 1500.0`
**Line:** `assert total_duration < 300.0, f"Large dataset workflow too slow: {total_duration:.2f}s"`

**File:** `tests/integration/test_end_to_end_workflows.py:566`
**Context:** `unknown_function`
**Current:** `total_duration < 300.0`
**Suggested:** `total_duration < 1500.0`
**Line:** `assert total_duration < 300.0, f"Large dataset workflow too slow: {total_duration:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:218`
**Context:** `load_configuration`
**Current:** `benchmark.stats.stats.mean < 1.0`
**Suggested:** `benchmark.stats.stats.mean < 5.0`
**Line:** `assert benchmark.stats.stats.mean < 1.0, f"Config loading too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:218`
**Context:** `load_configuration`
**Current:** `benchmark.stats.stats.mean < 1.0`
**Suggested:** `benchmark.stats.stats.mean < 5.0`
**Line:** `assert benchmark.stats.stats.mean < 1.0, f"Config loading too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:218`
**Context:** `load_configuration`
**Current:** `benchmark.stats.stats.mean < 1.0`
**Suggested:** `benchmark.stats.stats.mean < 5.0`
**Line:** `assert benchmark.stats.stats.mean < 1.0, f"Config loading too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:265`
**Context:** `parse_standard`
**Current:** `benchmark.stats.stats.mean < 2.0`
**Suggested:** `benchmark.stats.stats.mean < 10.0`
**Line:** `assert benchmark.stats.stats.mean < 2.0, f"Standard parsing too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:265`
**Context:** `parse_standard`
**Current:** `benchmark.stats.stats.mean < 2.0`
**Suggested:** `benchmark.stats.stats.mean < 10.0`
**Line:** `assert benchmark.stats.stats.mean < 2.0, f"Standard parsing too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:265`
**Context:** `parse_standard`
**Current:** `benchmark.stats.stats.mean < 2.0`
**Suggested:** `benchmark.stats.stats.mean < 10.0`
**Line:** `assert benchmark.stats.stats.mean < 2.0, f"Standard parsing too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:614`
**Context:** `test_assessment_sla_compliance`
**Current:** `duration < 10.0`
**Suggested:** `duration < 50.0`
**Line:** `assert duration < 10.0, f"Assessment SLA violation: {duration:.2f}s > 10s"`

**File:** `tests/performance/test_quality_benchmarks.py:614`
**Context:** `test_assessment_sla_compliance`
**Current:** `duration < 10.0`
**Suggested:** `duration < 50.0`
**Line:** `assert duration < 10.0, f"Assessment SLA violation: {duration:.2f}s > 10s"`

**File:** `tests/performance/test_quality_benchmarks.py:628`
**Context:** `test_standard_generation_sla_compliance`
**Current:** `duration < 30.0`
**Suggested:** `duration < 150.0`
**Line:** `assert duration < 30.0, f"Standard generation SLA violation: {duration:.2f}s > 30s"`

**File:** `tests/performance/test_quality_benchmarks.py:628`
**Context:** `test_standard_generation_sla_compliance`
**Current:** `duration < 30.0`
**Suggested:** `duration < 150.0`
**Line:** `assert duration < 30.0, f"Standard generation SLA violation: {duration:.2f}s > 30s"`

**File:** `tests/performance/test_quality_benchmarks.py:643`
**Context:** `test_profiling_sla_compliance`
**Current:** `duration < 45.0`
**Suggested:** `duration < 225.0`
**Line:** `assert duration < 45.0, f"Profiling SLA violation: {duration:.2f}s > 45s"`

**File:** `tests/performance/test_quality_benchmarks.py:643`
**Context:** `test_profiling_sla_compliance`
**Current:** `duration < 45.0`
**Suggested:** `duration < 225.0`
**Line:** `assert duration < 45.0, f"Profiling SLA violation: {duration:.2f}s > 45s"`

**File:** `tests/unit/validator/test_engine_comprehensive.py:575`
**Context:** `unknown_function`
**Current:** `sequential_duration < 30.0`
**Suggested:** `sequential_duration < 150.0`
**Line:** `assert sequential_duration < 30.0, f"Batch processing too slow: {sequential_duration:.2f}s"`

**File:** `tests/unit/validator/test_engine_comprehensive.py:575`
**Context:** `unknown_function`
**Current:** `sequential_duration < 30.0`
**Suggested:** `sequential_duration < 150.0`
**Line:** `assert sequential_duration < 30.0, f"Batch processing too slow: {sequential_duration:.2f}s"`

**File:** `tests/unit/analysis/test_type_inference_comprehensive.py:544`
**Context:** `unknown_function`
**Current:** `duration < 180.0`
**Suggested:** `duration < 900.0`
**Line:** `assert duration < 180.0, f"Wide dataset inference too slow: {duration:.2f}s"`

**File:** `tests/unit/analysis/test_type_inference_comprehensive.py:544`
**Context:** `unknown_function`
**Current:** `duration < 180.0`
**Suggested:** `duration < 900.0`
**Line:** `assert duration < 180.0, f"Wide dataset inference too slow: {duration:.2f}s"`

**File:** `tests/unit/analysis/test_standard_generator_comprehensive.py:521`
**Context:** `test_wide_dataset_generation_performance`
**Current:** `duration < 120.0`
**Suggested:** `duration < 600.0`
**Line:** `assert duration < 120.0, f"Wide dataset generation too slow: {duration:.2f}s"`

**File:** `tests/unit/analysis/test_standard_generator_comprehensive.py:521`
**Context:** `test_wide_dataset_generation_performance`
**Current:** `duration < 120.0`
**Suggested:** `duration < 600.0`
**Line:** `assert duration < 120.0, f"Wide dataset generation too slow: {duration:.2f}s"`

**File:** `tests/unit/analysis/test_data_profiler_comprehensive.py:421`
**Context:** `test_wide_dataset_profiling_performance`
**Current:** `duration < 60.0`
**Suggested:** `duration < 300.0`
**Line:** `assert duration < 60.0, f"Wide dataset profiling too slow: {duration:.2f}s"`

**File:** `tests/unit/analysis/test_data_profiler_comprehensive.py:421`
**Context:** `test_wide_dataset_profiling_performance`
**Current:** `duration < 60.0`
**Suggested:** `duration < 300.0`
**Line:** `assert duration < 60.0, f"Wide dataset profiling too slow: {duration:.2f}s"`

**File:** `tests/unit/config/test_loader_comprehensive.py:356`
**Context:** `unknown_function`
**Current:** `load_duration < 1.0`
**Suggested:** `load_duration < 5.0`
**Line:** `assert load_duration < 1.0, f"Config loading too slow: {load_duration:.2f}s"`

**File:** `tests/unit/config/test_loader_comprehensive.py:356`
**Context:** `unknown_function`
**Current:** `load_duration < 1.0`
**Suggested:** `load_duration < 5.0`
**Line:** `assert load_duration < 1.0, f"Config loading too slow: {load_duration:.2f}s"`

**File:** `tests/unit/config/test_loader_comprehensive.py:384`
**Context:** `unknown_function`
**Current:** `first_load_duration < 0.5`
**Suggested:** `first_load_duration < 2.5`
**Line:** `assert first_load_duration < 0.5, f"First load too slow: {first_load_duration:.2f}s"`

**File:** `tests/unit/config/test_loader_comprehensive.py:384`
**Context:** `unknown_function`
**Current:** `first_load_duration < 0.5`
**Suggested:** `first_load_duration < 2.5`
**Line:** `assert first_load_duration < 0.5, f"First load too slow: {first_load_duration:.2f}s"`

**File:** `tests/unit/config/test_loader_comprehensive.py:385`
**Context:** `unknown_function`
**Current:** `second_load_duration < 0.5`
**Suggested:** `second_load_duration < 2.5`
**Line:** `assert second_load_duration < 0.5, f"Second load too slow: {second_load_duration:.2f}s"`

**File:** `tests/unit/config/test_loader_comprehensive.py:385`
**Context:** `unknown_function`
**Current:** `second_load_duration < 0.5`
**Suggested:** `second_load_duration < 2.5`
**Line:** `assert second_load_duration < 0.5, f"Second load too slow: {second_load_duration:.2f}s"`

**File:** `tests/unit/logging/test_local_comprehensive.py:505`
**Context:** `unknown_function`
**Current:** `duration < 10.0`
**Suggested:** `duration < 50.0`
**Line:** `assert duration < 10.0, f"High volume logging too slow: {duration:.2f}s for {num_records} records"`

**File:** `tests/unit/logging/test_local_comprehensive.py:505`
**Context:** `unknown_function`
**Current:** `duration < 10.0`
**Suggested:** `duration < 50.0`
**Line:** `assert duration < 10.0, f"High volume logging too slow: {duration:.2f}s for {num_records} records"`

**File:** `tests/unit/logging/test_enterprise_comprehensive.py:423`
**Context:** `unknown_function`
**Current:** `duration < 30.0`
**Suggested:** `duration < 150.0`
**Line:** `assert duration < 30.0, f"High volume logging too slow: {duration:.2f}s for 1000 records"`

**File:** `tests/unit/logging/test_enterprise_comprehensive.py:423`
**Context:** `unknown_function`
**Current:** `duration < 30.0`
**Suggested:** `duration < 150.0`
**Line:** `assert duration < 30.0, f"High volume logging too slow: {duration:.2f}s for 1000 records"`

**File:** `tests/unit/logging/test_enterprise_comprehensive.py:427`
**Context:** `unknown_function`
**Current:** `duration < 30.0`
**Suggested:** `duration < 150.0`
**Line:** `assert duration < 30.0, f"Test took too long: {duration:.2f}s"`

**File:** `tests/unit/logging/test_enterprise_comprehensive.py:427`
**Context:** `unknown_function`
**Current:** `duration < 30.0`
**Suggested:** `duration < 150.0`
**Line:** `assert duration < 30.0, f"Test took too long: {duration:.2f}s"`

**File:** `tests/unit/standards/test_parser_comprehensive.py:410`
**Context:** `unknown_function`
**Current:** `small_duration < 0.1`
**Suggested:** `small_duration < 0.5`
**Line:** `assert small_duration < 0.1, f"Small standard parsing too slow: {small_duration:.2f}s"`

**File:** `tests/unit/standards/test_parser_comprehensive.py:410`
**Context:** `unknown_function`
**Current:** `small_duration < 0.1`
**Suggested:** `small_duration < 0.5`
**Line:** `assert small_duration < 0.1, f"Small standard parsing too slow: {small_duration:.2f}s"`

**File:** `tests/unit/standards/test_parser_comprehensive.py:454`
**Context:** `unknown_function`
**Current:** `large_duration < 1.0`
**Suggested:** `large_duration < 5.0`
**Line:** `assert large_duration < 1.0, f"Large standard parsing too slow: {large_duration:.2f}s"`

**File:** `tests/unit/standards/test_parser_comprehensive.py:454`
**Context:** `unknown_function`
**Current:** `large_duration < 1.0`
**Suggested:** `large_duration < 5.0`
**Line:** `assert large_duration < 1.0, f"Large standard parsing too slow: {large_duration:.2f}s"`

### Timing Processing (22 items)

**File:** `tests/performance/test_quality_benchmarks.py:69`
**Context:** `validate_data`
**Current:** `benchmark.stats.stats.mean < 10.0`
**Suggested:** `benchmark.stats.stats.mean < 30.0`
**Line:** `assert benchmark.stats.stats.mean < 10.0, f"Validation too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:69`
**Context:** `validate_data`
**Current:** `benchmark.stats.stats.mean < 10.0`
**Suggested:** `benchmark.stats.stats.mean < 30.0`
**Line:** `assert benchmark.stats.stats.mean < 10.0, f"Validation too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:69`
**Context:** `validate_data`
**Current:** `benchmark.stats.stats.mean < 10.0`
**Suggested:** `benchmark.stats.stats.mean < 30.0`
**Line:** `assert benchmark.stats.stats.mean < 10.0, f"Validation too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:91`
**Context:** `profile_data`
**Current:** `benchmark.stats.stats.mean < 15.0`
**Suggested:** `benchmark.stats.stats.mean < 45.0`
**Line:** `assert benchmark.stats.stats.mean < 15.0, f"Profiling too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:91`
**Context:** `profile_data`
**Current:** `benchmark.stats.stats.mean < 15.0`
**Suggested:** `benchmark.stats.stats.mean < 45.0`
**Line:** `assert benchmark.stats.stats.mean < 15.0, f"Profiling too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:91`
**Context:** `profile_data`
**Current:** `benchmark.stats.stats.mean < 15.0`
**Suggested:** `benchmark.stats.stats.mean < 45.0`
**Line:** `assert benchmark.stats.stats.mean < 15.0, f"Profiling too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:114`
**Context:** `generate_standard`
**Current:** `benchmark.stats.stats.mean < 20.0`
**Suggested:** `benchmark.stats.stats.mean < 60.0`
**Line:** `assert benchmark.stats.stats.mean < 20.0, f"Standard generation too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:114`
**Context:** `generate_standard`
**Current:** `benchmark.stats.stats.mean < 20.0`
**Suggested:** `benchmark.stats.stats.mean < 60.0`
**Line:** `assert benchmark.stats.stats.mean < 20.0, f"Standard generation too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:114`
**Context:** `generate_standard`
**Current:** `benchmark.stats.stats.mean < 20.0`
**Suggested:** `benchmark.stats.stats.mean < 60.0`
**Line:** `assert benchmark.stats.stats.mean < 20.0, f"Standard generation too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:136`
**Context:** `infer_types`
**Current:** `benchmark.stats.stats.mean < 5.0`
**Suggested:** `benchmark.stats.stats.mean < 15.0`
**Line:** `assert benchmark.stats.stats.mean < 5.0, f"Type inference too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:136`
**Context:** `infer_types`
**Current:** `benchmark.stats.stats.mean < 5.0`
**Suggested:** `benchmark.stats.stats.mean < 15.0`
**Line:** `assert benchmark.stats.stats.mean < 5.0, f"Type inference too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:136`
**Context:** `infer_types`
**Current:** `benchmark.stats.stats.mean < 5.0`
**Suggested:** `benchmark.stats.stats.mean < 15.0`
**Line:** `assert benchmark.stats.stats.mean < 5.0, f"Type inference too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:170`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 30.0`
**Suggested:** `benchmark.stats.stats.mean < 90.0`
**Line:** `assert benchmark.stats.stats.mean < 30.0, f"Data processing too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:170`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 30.0`
**Suggested:** `benchmark.stats.stats.mean < 90.0`
**Line:** `assert benchmark.stats.stats.mean < 30.0, f"Data processing too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:170`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 30.0`
**Suggested:** `benchmark.stats.stats.mean < 90.0`
**Line:** `assert benchmark.stats.stats.mean < 30.0, f"Data processing too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:588`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 25.0`
**Suggested:** `benchmark.stats.stats.mean < 75.0`
**Line:** `assert benchmark.stats.stats.mean < 25.0, f"Batch processing too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:588`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 25.0`
**Suggested:** `benchmark.stats.stats.mean < 75.0`
**Line:** `assert benchmark.stats.stats.mean < 25.0, f"Batch processing too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:588`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 25.0`
**Suggested:** `benchmark.stats.stats.mean < 75.0`
**Line:** `assert benchmark.stats.stats.mean < 25.0, f"Batch processing too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:648`
**Context:** `test_profiling_sla_compliance`
**Current:** `quality_score >= 70.0`
**Suggested:** `quality_score >= 210.0`
**Line:** `assert quality_score >= 70  # Quality maintained`

**File:** `tests/performance/test_quality_benchmarks.py:648`
**Context:** `test_profiling_sla_compliance`
**Current:** `quality_score >= 70.0`
**Suggested:** `quality_score >= 210.0`
**Line:** `assert quality_score >= 70  # Quality maintained`

**File:** `tests/unit/validator/dimensions/test_validity.py:107`
**Context:** `test_assess_with_validation_failures`
**Current:** `score < 18.0`
**Suggested:** `score < 54.0`
**Line:** `assert score < 18.0`

**File:** `tests/unit/validator/dimensions/test_validity.py:107`
**Context:** `test_assess_with_validation_failures`
**Current:** `score < 18.0`
**Suggested:** `score < 54.0`
**Line:** `assert score < 18.0`

### Quality Score (18 items)

**File:** `tests/performance/test_quality_benchmarks.py:88`
**Context:** `profile_data`
**Current:** `quality_score >= 70.0`
**Suggested:** `quality_score >= 60.0`
**Line:** `assert quality_score >= 70  # High quality data should score well`

**File:** `tests/performance/test_quality_benchmarks.py:88`
**Context:** `profile_data`
**Current:** `quality_score >= 70.0`
**Suggested:** `quality_score >= 60.0`
**Line:** `assert quality_score >= 70  # High quality data should score well`

**File:** `tests/performance/test_quality_benchmarks.py:340`
**Context:** `unknown_function`
**Current:** `avg_score >= 70.0`
**Suggested:** `avg_score >= 60.0`
**Line:** `assert avg_score >= 70  # Should maintain quality`

**File:** `tests/performance/test_quality_benchmarks.py:340`
**Context:** `unknown_function`
**Current:** `avg_score >= 70.0`
**Suggested:** `avg_score >= 60.0`
**Line:** `assert avg_score >= 70  # Should maintain quality`

**File:** `tests/performance/test_quality_benchmarks.py:671`
**Context:** `test_performance_quality_integration`
**Current:** `overall_performance >= 70.0`
**Suggested:** `overall_performance >= 60.0`
**Line:** `assert overall_performance >= 70.0, f"Performance quality below target: {overall_performance:.1f}%"`

**File:** `tests/performance/test_quality_benchmarks.py:671`
**Context:** `test_performance_quality_integration`
**Current:** `overall_performance >= 70.0`
**Suggested:** `overall_performance >= 60.0`
**Line:** `assert overall_performance >= 70.0, f"Performance quality below target: {overall_performance:.1f}%"`

**File:** `tests/unit/analysis/test_standard_generator_comprehensive.py:181`
**Context:** `unknown_function`
**Current:** `total_min_score >= 60.0`
**Suggested:** `total_min_score >= 60.0`
**Line:** `assert total_min_score >= 60.0  # Should sum to reasonable minimum`

**File:** `tests/unit/analysis/test_standard_generator_comprehensive.py:181`
**Context:** `unknown_function`
**Current:** `total_min_score >= 60.0`
**Suggested:** `total_min_score >= 60.0`
**Line:** `assert total_min_score >= 60.0  # Should sum to reasonable minimum`

**File:** `tests/unit/analysis/test_data_profiler_comprehensive.py:157`
**Context:** `test_data_quality_assessment`
**Current:** `high_profile.data_quality_score >= 80.0`
**Suggested:** `high_profile.data_quality_score >= 64.0`
**Line:** `assert high_profile.data_quality_score >= 80`

**File:** `tests/unit/analysis/test_data_profiler_comprehensive.py:157`
**Context:** `test_data_quality_assessment`
**Current:** `high_profile.data_quality_score >= 80.0`
**Suggested:** `high_profile.data_quality_score >= 64.0`
**Line:** `assert high_profile.data_quality_score >= 80`

**File:** `tests/unit/analysis/test_data_profiler_comprehensive.py:160`
**Context:** `test_data_quality_assessment`
**Current:** `low_profile.data_quality_score <= 91.0`
**Suggested:** `low_profile.data_quality_score <= 200.2`
**Line:** `assert low_profile.data_quality_score <= 91`

**File:** `tests/unit/analysis/test_data_profiler_comprehensive.py:160`
**Context:** `test_data_quality_assessment`
**Current:** `low_profile.data_quality_score <= 91.0`
**Suggested:** `low_profile.data_quality_score <= 200.2`
**Line:** `assert low_profile.data_quality_score <= 91`

**File:** `tests/unit/validator/dimensions/test_validity.py:60`
**Context:** `test_assess_with_field_requirements_simple`
**Current:** `score > 15.0`
**Suggested:** `score > 60.0`
**Line:** `assert score > 15.0  # Should be a good score`

**File:** `tests/unit/validator/dimensions/test_validity.py:60`
**Context:** `test_assess_with_field_requirements_simple`
**Current:** `score > 15.0`
**Suggested:** `score > 60.0`
**Line:** `assert score > 15.0  # Should be a good score`

**File:** `tests/unit/validator/dimensions/test_validity.py:87`
**Context:** `unknown_function`
**Current:** `score > 15.0`
**Suggested:** `score > 60.0`
**Line:** `assert score > 15.0`

**File:** `tests/unit/validator/dimensions/test_validity.py:87`
**Context:** `unknown_function`
**Current:** `score > 15.0`
**Suggested:** `score > 60.0`
**Line:** `assert score > 15.0`

**File:** `tests/unit/validator/dimensions/test_validity.py:234`
**Context:** `unknown_function`
**Current:** `score < 20.0`
**Suggested:** `score < 44.0`
**Line:** `assert score < 20.0  # Should have some failures`

**File:** `tests/unit/validator/dimensions/test_validity.py:234`
**Context:** `unknown_function`
**Current:** `score < 20.0`
**Suggested:** `score < 44.0`
**Line:** `assert score < 20.0  # Should have some failures`

### Timing Workflow (9 items)

**File:** `tests/performance/test_quality_benchmarks.py:306`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 60.0`
**Suggested:** `benchmark.stats.stats.mean < 120.0`
**Line:** `assert benchmark.stats.stats.mean < 60.0, f"Memory-intensive workflow too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:306`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 60.0`
**Suggested:** `benchmark.stats.stats.mean < 120.0`
**Line:** `assert benchmark.stats.stats.mean < 60.0, f"Memory-intensive workflow too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:306`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 60.0`
**Suggested:** `benchmark.stats.stats.mean < 120.0`
**Line:** `assert benchmark.stats.stats.mean < 60.0, f"Memory-intensive workflow too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:389`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 45.0`
**Suggested:** `benchmark.stats.stats.mean < 90.0`
**Line:** `assert benchmark.stats.stats.mean < 45.0, f"Complete workflow too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:389`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 45.0`
**Suggested:** `benchmark.stats.stats.mean < 90.0`
**Line:** `assert benchmark.stats.stats.mean < 45.0, f"Complete workflow too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:389`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 45.0`
**Suggested:** `benchmark.stats.stats.mean < 90.0`
**Line:** `assert benchmark.stats.stats.mean < 45.0, f"Complete workflow too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:550`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 5.0`
**Suggested:** `benchmark.stats.stats.mean < 10.0`
**Line:** `assert benchmark.stats.stats.mean < 5.0, f"Resource-efficient workflow too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:550`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 5.0`
**Suggested:** `benchmark.stats.stats.mean < 10.0`
**Line:** `assert benchmark.stats.stats.mean < 5.0, f"Resource-efficient workflow too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:550`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 5.0`
**Suggested:** `benchmark.stats.stats.mean < 10.0`
**Line:** `assert benchmark.stats.stats.mean < 5.0, f"Resource-efficient workflow too slow: {benchmark.stats.stats.mean:.2f}s"`

### Benchmark Performance (6 items)

**File:** `tests/performance/test_quality_benchmarks.py:343`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 15.0`
**Suggested:** `benchmark.stats.stats.mean < 45.0`
**Line:** `assert benchmark.stats.stats.mean < 15.0, f"Concurrent operations too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:343`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 15.0`
**Suggested:** `benchmark.stats.stats.mean < 45.0`
**Line:** `assert benchmark.stats.stats.mean < 15.0, f"Concurrent operations too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:343`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 15.0`
**Suggested:** `benchmark.stats.stats.mean < 45.0`
**Line:** `assert benchmark.stats.stats.mean < 15.0, f"Concurrent operations too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:495`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 120.0`
**Suggested:** `benchmark.stats.stats.mean < 360.0`
**Line:** `assert benchmark.stats.stats.mean < 120.0, f"Stress test too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:495`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 120.0`
**Suggested:** `benchmark.stats.stats.mean < 360.0`
**Line:** `assert benchmark.stats.stats.mean < 120.0, f"Stress test too slow: {benchmark.stats.stats.mean:.2f}s"`

**File:** `tests/performance/test_quality_benchmarks.py:495`
**Context:** `unknown_function`
**Current:** `benchmark.stats.stats.mean < 120.0`
**Suggested:** `benchmark.stats.stats.mean < 360.0`
**Line:** `assert benchmark.stats.stats.mean < 120.0, f"Stress test too slow: {benchmark.stats.stats.mean:.2f}s"`
