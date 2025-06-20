# ADRI Provenance Specification v1.0

## Overview

This specification defines how ADRI will implement cryptographic provenance chains to ensure data assessment integrity and auditability. This is a future implementation guide - the current ADRI release includes the necessary structure to support this feature but does not yet implement the full provenance system.

## 1. Provenance Data Structure

### Core Provenance Block
```python
<!-- audience: ai-builders -->
@dataclass
class ProvenanceBlock:
    """Immutable provenance information for an assessment"""
    
    # Dataset identification
    dataset: DatasetHash
    
    # Template identification  
    template: TemplateHash
    
    # Test verification
    tests: TestBundleHash
    
    # Assessment context
    assessment: AssessmentContext
    
    # Cryptographic signature
    signature: ProvenanceSignature
```

### Dataset Hash Structure
```python
<!-- audience: ai-builders -->
@dataclass
class DatasetHash:
    algorithm: str = "sha256-merkle"  # For large datasets
    hash: str  # Primary hash
    size_bytes: int
    row_count: int
    column_count: int
    column_fingerprint: str  # Hash of column names/types
    sample_hash: str  # Hash of first 1000 rows for quick verification
```

### Template Hash Structure
```python
<!-- audience: ai-builders -->
@dataclass
class TemplateHash:
    template_id: str
    version: str
    content_hash: str  # SHA256 of template YAML
    authority: str
    effective_date: str
```

### Test Bundle Hash Structure
```python
<!-- audience: ai-builders -->
@dataclass 
class TestBundleHash:
    bundle_id: str
    bundle_hash: str  # SHA256 of all test files
    test_manifest: List[TestFileHash]
    coverage_report_hash: str  # Hash of coverage report
    
@dataclass
class TestFileHash:
    filename: str
    hash: str
    rule_ids: List[str]  # Rules tested by this file
```

### Assessment Context
```python
<!-- audience: ai-builders -->
@dataclass
class AssessmentContext:
    timestamp: datetime
    adri_version: str
    engine_hash: str  # Hash of ADRI core modules
    config_hash: str  # Hash of configuration used
    environment: Dict[str, str]  # Python version, key packages
```

### Provenance Signature
```python
<!-- audience: ai-builders -->
@dataclass
class ProvenanceSignature:
    algorithm: str = "sha256"
    signature: str  # Hash of entire provenance block
    signed_at: datetime
```

## 2. Hashing Strategies

### 2.1 Dataset Hashing

For efficient hashing of datasets of any size:

```python
<!-- audience: ai-builders -->
class DatasetHasher:
    """Efficient hashing for datasets of any size"""
    
    def hash_dataset(self, data: Union[pd.DataFrame, str]) -> DatasetHash:
        if isinstance(data, pd.DataFrame):
            return self._hash_dataframe(data)
        else:
            return self._hash_file(data)
    
    def _hash_dataframe(self, df: pd.DataFrame) -> DatasetHash:
        # For small datasets (<100MB): full content hash
        if df.memory_usage(deep=True).sum() < 100_000_000:
            return self._full_hash(df)
        
        # For large datasets: Merkle tree approach
        return self._merkle_hash(df)
    
    def _merkle_hash(self, df: pd.DataFrame) -> DatasetHash:
        """Build Merkle tree for efficient verification"""
        # 1. Hash each chunk of 10k rows
        # 2. Build tree from chunk hashes
        # 3. Return root hash + tree structure
```

### 2.2 Template Hashing

```python
<!-- audience: ai-builders -->
def hash_template(template_path: str) -> TemplateHash:
    """Hash template content and metadata"""
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Parse to ensure it's valid
    template_data = yaml.safe_load(content)
    
    return TemplateHash(
        template_id=template_data['template']['id'],
        version=template_data['template']['version'],
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
        authority=template_data['template']['authority'],
        effective_date=template_data['template'].get('effective_date')
    )
```

### 2.3 Test Bundle Hashing

```python
<!-- audience: ai-builders -->
def hash_test_bundle(bundle_path: str) -> TestBundleHash:
    """Hash all test files in a bundle"""
    manifest = load_bundle_manifest(bundle_path)
    
    file_hashes = []
    for test_file in manifest['tests']:
        with open(test_file['path'], 'rb') as f:
            content = f.read()
        
        file_hashes.append(TestFileHash(
            filename=test_file['path'],
            hash=hashlib.sha256(content).hexdigest(),
            rule_ids=test_file['rule_ids']
        ))
    
    # Combine all file hashes
    combined = ''.join(fh.hash for fh in file_hashes)
    bundle_hash = hashlib.sha256(combined.encode()).hexdigest()
    
    return TestBundleHash(
        bundle_id=manifest['bundle_id'],
        bundle_hash=bundle_hash,
        test_manifest=file_hashes,
        coverage_report_hash=hash_coverage_report(bundle_path)
    )
```

## 3. Test Bundle Organization

### Directory Structure
```
tests/bundles/
├── manifest.yaml  # Global manifest
├── financial/
│   └── basel-iii-v1.0.0/
│       ├── bundle.yaml  # Bundle manifest
│       ├── test_validity_rules.py
│       ├── test_completeness_rules.py
│       └── coverage.xml
├── general/
│   └── production-v1.0.0/
│       ├── bundle.yaml
│       └── test_*.py
```

### Bundle Manifest Format
```yaml
bundle:
  template_id: "financial/basel-iii"
  template_version: "1.0.0"
  created_at: "2024-01-15T10:00:00Z"
  
rules:
  - rule_id: "validity.type_consistency"
    test_file: "test_validity_rules.py::TestTypeConsistency"
  - rule_id: "completeness.missing_value"
    test_file: "test_completeness_rules.py::TestMissingValue"
    
coverage:
  overall: 98.5
  by_rule:
    "validity.type_consistency": 100.0
    "completeness.missing_value": 97.0
```

## 4. Verification API

### 4.1 Verification Levels

```python
<!-- audience: ai-builders -->
class ProvenanceVerifier:
    """Verify provenance chains"""
    
    def verify_report(self, report_path: str, dataset_path: str = None) -> VerificationResult:
        """Full verification of a report's provenance"""
        report = self.load_report(report_path)
        
        # Level 1: Signature verification (fast)
        if not self.verify_signature(report.provenance):
            return VerificationResult(valid=False, reason="Invalid signature")
        
        # Level 2: Template verification (medium)
        if not self.verify_template(report.provenance.template):
            return VerificationResult(valid=False, reason="Template modified")
        
        # Level 3: Test bundle verification (slow, optional)
        if self.strict_mode:
            if not self.verify_tests(report.provenance.tests):
                return VerificationResult(valid=False, reason="Tests modified")
        
        # Level 4: Dataset verification (very slow, if provided)
        if dataset_path:
            if not self.verify_dataset(dataset_path, report.provenance.dataset):
                return VerificationResult(valid=False, reason="Dataset modified")
        
        return VerificationResult(valid=True)
```

### 4.2 Quick Verification

```python
<!-- audience: ai-builders -->
def quick_verify(self, report: ADRIReport, df: pd.DataFrame) -> bool:
    """Fast verification for guards"""
    # Just check dataset sample hash (first 1000 rows)
    sample = df.head(1000)
    sample_hash = self.hash_sample(sample)
    
    return sample_hash == report.provenance.dataset.sample_hash
```

## 5. CLI Commands

### Generate Provenance
```bash
# Generate provenance info during assessment
adri assess data.csv --with-provenance

# Output includes provenance block
{
  "adri_score_report": {...},
  "provenance": {
    "dataset": {...},
    "template": {...},
    "signature": "sha256:..."
  }
}
```

### Verify Provenance
```bash
# Full verification
adri verify-provenance report.json --dataset data.csv --strict

# Quick verification (signature only)
adri verify-provenance report.json --quick

# Show provenance details
adri show-provenance report.json
```

### Test Bundle Management
```bash
# Create test bundle for template
adri create-test-bundle financial/basel-iii --output-dir ./bundles/

# Verify test bundle
adri verify-test-bundle ./bundles/financial/basel-iii-v1.0.0/
```

## 6. Guard Integration

### 6.1 Guard with Provenance

```python
<!-- audience: ai-builders -->
@adri_guarded(
    template="financial/basel-iii",
    verify_provenance=True,
    cache_ttl=3600  # Cache verification for 1 hour
)
def process_financial_data(df: pd.DataFrame):
    """Guard verifies provenance before execution"""
    # Guard automatically:
    # 1. Computes hash of df
    # 2. Looks for matching ADRI report
    # 3. Verifies provenance chain
    # 4. Allows/blocks execution based on verification
    return analyze(df)
```

### 6.2 Guard Verification Flow

```python
<!-- audience: ai-builders -->
class ProvenanceGuard:
    def verify_data(self, df: pd.DataFrame, report: ADRIReport) -> bool:
        # 1. Quick hash comparison (sample)
        if not self.quick_verify(df, report):
            return False
            
        # 2. Check cache
        cache_key = f"{report.provenance.signature}:{df.shape}"
        if self.is_cached(cache_key):
            return True
            
        # 3. Full verification (if needed)
        if self.strict_mode:
            result = self.full_verify(df, report)
            if result:
                self.cache_result(cache_key, self.cache_ttl)
            return result
            
        return True
```

## 7. Performance Optimizations

### 7.1 Hashing Performance

| Dataset Size | Strategy | Time | Memory |
|-------------|----------|------|---------|
| < 100MB | Full SHA-256 | < 1s | Low |
| 100MB - 1GB | Merkle Tree | < 5s | Medium |
| > 1GB | Streaming + Sampling | < 10s | Low |

### 7.2 Caching Strategy

```python
<!-- audience: ai-builders -->
class ProvenanceCache:
    """LRU cache for verification results"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = LRUCache(max_size)
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[bool]:
        entry = self.cache.get(key)
        if entry and time.time() - entry.timestamp < self.ttl:
            return entry.result
        return None
```

### 7.3 Parallel Processing

```python
<!-- audience: ai-builders -->
def parallel_hash_large_dataset(df: pd.DataFrame, num_workers: int = 4) -> str:
    """Hash large dataset using multiple workers"""
    chunk_size = len(df) // num_workers
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i in range(num_workers):
            start = i * chunk_size
            end = start + chunk_size if i < num_workers - 1 else len(df)
            chunk = df.iloc[start:end]
            futures.append(executor.submit(hash_chunk, chunk))
        
        chunk_hashes = [f.result() for f in futures]
    
    # Combine chunk hashes
    return combine_hashes(chunk_hashes)
```

## 8. Security Considerations

### 8.1 Hash Algorithm Selection
- **Default**: SHA-256 (widely supported, sufficient for most use cases)
- **High Security**: SHA-3-256 (quantum-resistant)
- **Performance**: BLAKE3 (faster for large datasets)

### 8.2 Timing Attack Prevention
```python
<!-- audience: ai-builders -->
def constant_time_compare(a: str, b: str) -> bool:
    """Compare hashes in constant time"""
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    
    return result == 0
```

### 8.3 Future: Digital Signatures
```python
<!-- audience: ai-builders -->
# Future enhancement: Sign provenance with private key
class SignedProvenance:
    def sign(self, private_key: str) -> str:
        """Sign provenance block with private key"""
        # Implementation for PKI-based signing
        pass
    
    def verify(self, public_key: str, signature: str) -> bool:
        """Verify signature with public key"""
        # Implementation for signature verification
        pass
```

## 9. Migration Path

### Phase 1: Current Release (Implemented)
- ✅ Report structure with metadata field
- ✅ Provenance placeholder in reports
- ✅ Template matching with confidence
- ✅ Generic fallback template

### Phase 2: Basic Provenance (Next Release)
- Dataset hashing (simple SHA-256)
- Template content hashing
- Basic signature generation
- CLI verification commands

### Phase 3: Full Implementation
- Merkle tree for large datasets
- Test bundle organization
- Guard integration
- Performance optimizations

### Phase 4: Enterprise Features
- Digital signatures with PKI
- Distributed verification
- Blockchain integration (optional)
- Compliance reporting

## 10. Example Usage

### Basic Provenance Check
```python
<!-- audience: ai-builders -->
# Assess with provenance
assessor = DataSourceAssessor()
report = assessor.assess_file("data.csv", with_provenance=True)

# Later, verify the data hasn't changed
verifier = ProvenanceVerifier()
is_valid = verifier.verify_dataset("data.csv", report.provenance.dataset)
```

### Guard with Cached Verification
```python
<!-- audience: ai-builders -->
@adri_guarded(
    template="production-v1.0.0",
    verify_provenance=True,
    cache_ttl=7200  # 2 hours
)
def process_production_data(df: pd.DataFrame):
    # First call: Full verification
    # Subsequent calls within 2 hours: Use cache
    return transform_data(df)
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Verify Data Provenance
  run: |
    adri verify-provenance report.json --dataset data.csv
    if [ $? -ne 0 ]; then
      echo "Data integrity check failed!"
      exit 1
    fi
```

## Summary

This provenance system will provide:
1. **Immutable audit trails** - Complete history of assessments
2. **Data integrity** - Detect any changes to data/templates/tests
3. **Performance** - Efficient verification through caching and optimization
4. **Flexibility** - Multiple verification levels for different use cases
5. **Future-proof** - Ready for digital signatures and blockchain

The current ADRI release includes the necessary structure to support this system, making it easy to add provenance features in future releases without breaking changes.
