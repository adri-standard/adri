# Troubleshooting

## Common Issues

### Import Errors

```bash
ModuleNotFoundError: No module named 'adri'
```

**Solution**: Ensure ADRI is installed: `pip install adri`

### Memory Issues

Large datasets may cause memory issues.

**Solution**: Use sampling or chunked processing:

```python
<!-- audience: ai-builders -->
# Sample large datasets
sampled_data = data.sample(n=10000)
results = assessor.assess(sampled_data)
```

### Performance Issues

**Solution**: Enable parallel processing:

```python
<!-- audience: standard-contributors -->
assessor = Assessor(parallel=True, n_jobs=4)
```
