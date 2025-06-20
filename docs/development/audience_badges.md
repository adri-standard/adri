# Audience Badges in ADRI Documentation

This guide explains how to use audience badges in ADRI documentation to clearly indicate which parts of the documentation are intended for specific audience types.

## Audience Types

ADRI serves three primary audiences, each with distinct needs and roles in the AI data ecosystem:

1. **🤖 AI Builders** - Developers building AI applications and agents
2. **📊 Data Providers** - Teams that manage, prepare, and deliver data for AI systems
3. **🛠️ Standard Contributors** - Open source contributors and organizations improving ADRI

## Using Audience Badges

There are two main ways to use audience badges in your documentation:

### 1. Inline Audience Badges

Use inline audience badges to mark specific paragraphs or sections of content:

```html
<span class="audience-badge audience-badge-ai-builder"><span class="emoji">🤖</span> AI Builder</span>
<span class="audience-badge audience-badge-data-provider"><span class="emoji">📊</span> Data Provider</span>
<span class="audience-badge audience-badge-standard-contributor"><span class="emoji">🛠️</span> Standard Contributor</span>
```

### 2. Audience-Specific Headings

Add audience indicators to headings using the `data-audience` attribute:

```html
<h3 data-audience="AI_BUILDER">This heading is for AI Builders</h3>
<h3 data-audience="DATA_PROVIDER">This heading is for Data Providers</h3>
<h3 data-audience="STANDARD_CONTRIBUTOR">This heading is for Standard Contributors</h3>
```

## Audience Badge Colors

Each audience type has a specific color to help with visual identification:

- **AI Builders**: Blue (#3b82f6)
- **Data Providers**: Green (#10b981)
- **Standard Contributors**: Purple (#8b5cf6)

## When to Use Audience Badges

Use audience badges in the following situations:

1. **Section-specific content**: When a section of documentation is primarily relevant to one audience type
2. **Technical complexity**: When explaining concepts that have different implications for different audiences
3. **Role-specific instructions**: When providing instructions that are specific to certain roles
4. **Implementation guidance**: When offering guidance that varies based on the reader's role

## Example Usage

Here's an example of how to use audience badges in your documentation:

```markdown
# Data Quality Assessment

<span class="audience-badge audience-badge-data-provider"><span class="emoji">📊</span> Data Provider</span>

This section explains how to assess the quality of your data before making it available to AI systems.

## Setting Up Quality Checks

<span class="audience-badge audience-badge-ai-builder"><span class="emoji">🤖</span> AI Builder</span>

AI Builders should configure quality thresholds based on their specific use case requirements.

<h3 data-audience="DATA_PROVIDER">Implementing Data Validation</h3>

Data Providers should implement the following validation checks...

<h3 data-audience="STANDARD_CONTRIBUTOR">Extending the Validation Framework</h3>

Standard Contributors can extend the validation framework by...
```

## Live Example

For a live example of audience badges in action, see the [Audience Badges Example](../../examples/documentation/audience_badges_example.html) page.

## Implementation Details

The audience badge styles are defined in `docs/assets/styles.css`. The CSS includes:

1. Styles for inline badges (`.audience-badge`, `.audience-badge-ai-builder`, etc.)
2. Styles for heading badges using the `data-audience` attribute
3. Responsive design considerations for different screen sizes

## Best Practices

1. **Be selective**: Don't overuse badges - only use them when content is truly audience-specific
2. **Be consistent**: Use the same badge type for similar content throughout the documentation
3. **Provide context**: Even with badges, ensure content is understandable with sufficient context
4. **Consider all audiences**: Try to make most content accessible to all audiences when possible
5. **Use with headings**: Prefer using badges with headings to clearly delineate sections

---

*Last Updated: June 20, 2025*
