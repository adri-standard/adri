## Description

Please include a summary of the changes and which issue is fixed. Include relevant motivation and context.

Fixes #(issue number)

## Type of change

Please delete options that are not relevant.

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Template contribution (new industry template)
- [ ] Performance improvement
- [ ] Code refactoring

## Checklist

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published in downstream modules

## Testing

Please describe the tests that you ran to verify your changes:

- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

### Test configuration
- Python version:
- Operating System:

## ADRI Specific Checks

For changes affecting data assessment:
- [ ] Changes maintain backward compatibility with existing templates
- [ ] New rules follow the standard rule interface
- [ ] Dimension scores remain in 0-100 range
- [ ] Business impact messages are clear and actionable

For new templates:
- [ ] Template follows naming convention: `adri-{industry}-{usecase}-v{version}`
- [ ] Includes comprehensive documentation
- [ ] Provides example data files
- [ ] Has been tested with real-world data

## Additional Information

Any additional information or context about the pull request.
