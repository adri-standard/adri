# Development Guide

This guide outlines the development process, code quality standards, and implementation methodology for the Constrained AI Agent System.

## Implementation Methodology

This document is a key reference that outlines the structured approach we use for AI-assisted development of the project. It should be one of the first documents that an AI reads when working on this project.

### Four-Role Development Approach

Our development process utilizes four distinct roles that the AI assistant transitions between:

**Important**: In all roles do not alter the planned solution architecture or build process if you hit a blocker without first confirming this with a human user.

#### 1. Developer Role

**Purpose**: Implementation of functional code that meets requirements

**Responsibilities**:
- Writing clean, efficient code that follows project standards
- Implementing features according to specifications
- Creating and updating unit tests
- Handling edge cases and error conditions

**Working Style**:
- Focus on pragmatic solutions
- Prioritize functionality while maintaining quality
- Iterative development with regular feedback requested after each file update from the other roles in the project
- After each new small feature is completed a review is triggered with the Reviewer roles and other defined roles
- Ensures where it is not clear on what to implement asks for clear direction from the human in the loop with specific options on what it recommends with details on why this aligns with the project briefs objectives

**Transition Trigger**: File and/or Component implementation is complete

#### 2. Reviewer Role

**Purpose**: Critical analysis of code for quality, efficiency, and correctness

**Responsibilities**:
- Identifying code smells and inefficiencies
- Checking for edge cases and error handling
- Ensuring adherence to project coding standards
- Suggesting improvements and optimizations

**Working Style**:
- Constructive criticism with clear rationale
- Focus on specific, actionable feedback
- Systematic review using established checklist

**Transition Trigger**: Review complete with no issues (or issues addressed)

#### 3. Technical Architect Role

**Purpose**: Documentation of design decisions and architecture

**Responsibilities**:
- Updating and maintaining the Solution guide to ensure it reflects actual implementation
- Documenting design decisions and rationales
- Ensuring architectural consistency
- Maintaining technical specifications

**Working Style**:
- Focus on clarity and accessibility of documentation
- Use of diagrams and examples to illustrate concepts
- Consideration of future developers' needs

**Transition Trigger**: Documentation updates complete

#### 4. Continuity Manager Role

**Purpose**: Ensuring knowledge transfer between development sessions

**Responsibilities**:
- Reloads this methodology every 20 API calls in a conversation to ensure everyone remembers their roles in the project
- Ensure the project brief is being followed in implementation
- Maintaining the session brief document
- Maintaining comprehensive project state and progress log that adheres with original brief
- Documenting environment and context information
- Documenting decisions made and reasons why
- Interacting and asking help from the human users that is specific clear and actionable

**Working Style**:
- Meticulous attention to detail
- Focus on capturing context and rationale
- Organization of information for quick retrieval

**Transition Trigger**: Actioned every 10 API Calls with each stakeholder and/or when a component or feature is completed

### Role Transition Process

1. **Explicit Announcement**: The AI clearly states when it's transitioning roles
2. **Context Establishment**: Brief summary of the current state relevant to the new role
3. **Previous Role Summary**: Quick summary of what was accomplished in the previous role
4. **New Role Priorities**: Clear statement of what the new role will focus on

### Collaboration Guidelines

#### For the Human Collaborator
- Request specific role engagement when needed
- Provide feedback on role performance
- Alert the AI when approaching the end of a session
- Share preferences for documentation and handover formats

#### For the AI Assistant
- Clearly indicate current active role
- Maintain consistent formatting for each role's outputs
- Provide rationale for significant decisions in each role
- Update session brief at key milestones

### Document Management

- **Session Brief**: Updated continually throughout active development
- **Project log**: Created and maintained by the continuity manager role
- **Solution Guide**: Updated when design changes occurs 
- **Implementation Guide**: Updated when process changes are made
- **How to guide**: Updated and maintained when new functionality is being reviewed

### Principles for Implementation

- **Methodology**: Use an agile methodology ensuring that we are building a Minimum viable solution at all times that can be tested as it is being built. Do not build in a waterfall approach.
- **Iterative Development**: Build features incrementally and test them as you go.
- **Feedback Loop**: Regularly seek feedback from other team members and stakeholders.
- **Documentation**: Keep documentation up-to-date as the code evolves.

## Code Quality Standards

### Code Style

The project follows these code style guidelines:

#### Python

- **Formatting**: Use Black for automatic formatting
- **Import Sorting**: Use isort for organizing imports
- **Type Checking**: Use mypy for static type checking
- **Linting**: Use flake8 for code quality checks
- **Docstrings**: Use Google-style docstrings

#### Running Code Quality Checks

To ensure code quality, run the following commands before committing changes:

```bash
# Format code with Black (line length of 79 characters)
python -m black --line-length 79 adri/

# Sort imports with isort
python -m isort adri/

# Run flake8 linting
python -m flake8 adri/

# Run mypy type checking
python -m mypy adri/
```

#### Mypy Configuration

The project includes a `mypy.ini` configuration file to manage type checking:

```ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True

[mypy.plugins.numpy.*]
follow_imports = skip

[mypy.plugins.pandas.*]
follow_imports = skip

[mypy.plugins.matplotlib.*]
follow_imports = skip

[mypy-inquirer.*]
ignore_missing_imports = True

# Add module-specific configurations as needed
```

For third-party libraries without type stubs, use one of these approaches:
1. Add `# type: ignore` comments to imports
2. Add module-specific configurations to `mypy.ini`
3. Install type stubs (e.g., `pip install pandas-stubs types-PyYAML`)

Example:

```python
def calculate_total(items: List[Item], discount: float = 0.0) -> float:
    """Calculate the total price of items with an optional discount.
    
    Args:
        items: A list of Item objects to calculate the total for.
        discount: A discount percentage as a decimal (e.g., 0.1 for 10%).
        
    Returns:
        The total price after applying the discount.
        
    Raises:
        ValueError: If discount is negative or greater than 1.
    """
    if discount < 0 or discount > 1:
        raise ValueError("Discount must be between 0 and 1")
        
    subtotal = sum(item.price for item in items)
    return subtotal * (1 - discount)
```

#### JavaScript/TypeScript

- **Formatting**: Use Prettier for automatic formatting
- **Linting**: Use ESLint for code quality checks
- **Type Checking**: Use TypeScript for static type checking
- **Import Sorting**: Use ESLint import plugin for organizing imports

Example:

```typescript
/**
 * Calculate the total price of items with an optional discount.
 * 
 * @param items - A list of Item objects to calculate the total for.
 * @param discount - A discount percentage as a decimal (e.g., 0.1 for 10%).
 * @returns The total price after applying the discount.
 * @throws Error if discount is negative or greater than 1.
 */
function calculateTotal(items: Item[], discount: number = 0): number {
    if (discount < 0 || discount > 1) {
        throw new Error("Discount must be between 0 and 1");
    }
    
    const subtotal = items.reduce((sum, item) => sum + item.price, 0);
    return subtotal * (1 - discount);
}
```

### Code Organization

#### Python

- **Module Structure**: Organize code into modules by functionality
- **Class Structure**: Use classes to encapsulate related functionality
- **Function Length**: Keep functions short and focused on a single task


### Testing Standards

#### P1 Testing Principle

- **Test Quality is Critical**: Testing must meet the highest standards and verify that the application meets business needs. Tests should accurately reflect how the application works in production, without shortcuts or hacks that degrade the ability to properly test the code. Users may read tests to understand how the application works, so tests should be clear, comprehensive, and representative of real-world usage.

#### Test Types

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test the entire system from user input to output

#### Test Coverage

- **Minimum Coverage**: Aim for at least 80% code coverage
- **Critical Paths**: Ensure 100% coverage of critical paths
- **Edge Cases**: Include tests for edge cases and error conditions

#### Test Environment Integrity

- **Production-Like Testing**: Tests should run in an environment that closely resembles production.
- **No Test-Only Hacks**: Avoid creating test-specific hacks or shortcuts that wouldn't exist in production code.
- **Fix Underlying Issues**: When tests fail, fix the underlying code issues rather than modifying tests to work around them.
- **Dependency Management**: Ensure all dependencies (databases, services, etc.) are properly configured for testing.

#### Test Structure

- **Arrange-Act-Assert**: Structure tests using the AAA pattern
- **Test Isolation**: Each test should be independent of others
- **Descriptive Names**: Use descriptive test names that explain what is being tested

Example:

```python
def test_calculate_total_with_discount():
    # Arrange
    items = [Item(price=10.0), Item(price=20.0)]
    discount = 0.1
    
    # Act
    result = calculate_total(items, discount)
    
    # Assert
    assert result == 27.0  # (10 + 20) * 0.9 = 27
```

### Error Handling

- **Explicit Exceptions**: Use explicit exception types
- **Meaningful Messages**: Provide meaningful error messages
- **Graceful Degradation**: Handle errors gracefully and provide fallbacks when possible
- **Logging**: Log errors with appropriate context for debugging

Example:

```python
try:
    result = process_data(data)
except ValidationError as e:
    logger.error(f"Validation error processing data: {str(e)}")
    raise HTTPException(status_code=400, detail=str(e))
except DatabaseError as e:
    logger.error(f"Database error processing data: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Documentation Standards

- **Code Comments**: Use comments to explain why, not what
- **Docstrings**: Document all public functions, classes, and modules
- **README**: Keep the README up-to-date with setup and usage instructions
- **Architecture Documentation**: Document the system architecture and design decisions
- **API Documentation**: Document all API endpoints and their parameters

## Implementation Methodology

### Agile Development

The project follows an agile development methodology:

- **Sprints**: Work is organized into 2-week sprints
- **User Stories**: Features are defined as user stories
- **Story Points**: User stories are estimated in story points
- **Daily Standups**: Team members share progress and blockers daily
- **Sprint Reviews**: The team reviews completed work at the end of each sprint
- **Sprint Retrospectives**: The team reflects on the sprint and identifies improvements

### Continuous Integration and Deployment

- **Automated Testing**: All code changes are automatically tested
- **Code Quality Checks**: Code quality is automatically checked
- **Continuous Deployment**: Changes are automatically deployed to staging
- **Manual Approval**: Production deployments require manual approval

### Version Control

- **Git Flow**: The project uses the Git Flow branching model
- **Feature Branches**: New features are developed in feature branches
- **Pull Requests**: Changes are reviewed through pull requests
- **Commit Messages**: Commit messages follow the Conventional Commits format

Example commit message:

```
feat(slack): add support for interactive buttons

Add support for interactive buttons in Slack messages to improve user experience.

Closes #123
```

### Issue Tracking

- **Issue Types**: Issues are categorized as bugs, features, or tasks
- **Priority Levels**: Issues are assigned priority levels
- **Assignees**: Issues are assigned to specific team members
- **Labels**: Issues are labeled for easy filtering
- **Milestones**: Issues are grouped into milestones for release planning

## Development Environment Setup

### Prerequisites

- **Git**: Required for version control
- **Visual Studio Code**: Recommended IDE

### IDE Configuration

#### Visual Studio Code

Install the following extensions:

- **Python**: For Python language support
- **Pylance**: For Python type checking
- **Black Formatter**: For Python code formatting
- **isort**: For Python import sorting
- **ESLint**: For JavaScript/TypeScript linting
- **Prettier**: For JavaScript/TypeScript formatting
- **Markdown All in One**: For Markdown editing
- **Mermaid Preview**: For previewing Mermaid diagrams

Configure settings:

```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### Local Development

## Contribution Guidelines

### Pull Request Process

1. Create a feature branch from the develop branch
2. Implement your changes
3. Write tests for your changes
4. Update documentation as needed
5. Submit a pull request to the develop branch
6. Address any review comments
7. Once approved, your changes will be merged

### Code Review Checklist

- [ ] Code follows the project's style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No unnecessary dependencies are added
- [ ] No sensitive information is included
- [ ] Error handling is appropriate
- [ ] Performance considerations are addressed
- [ ] Security considerations are addressed

### Commit Message Guidelines

Follow the Conventional Commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Where:
- **type**: feat, fix, docs, style, refactor, test, chore
- **scope**: The scope of the change (e.g., slack, verodat, workflow)
- **subject**: A short description of the change
- **body**: A more detailed description of the change
- **footer**: References to issues, breaking changes, etc.
