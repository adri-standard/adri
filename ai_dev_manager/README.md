# AI Dev Manager for ADRI

This directory contains resources and documentation for AI-assisted development of the Agent Data Readiness Index (ADRI) project. It follows the structured AI Dev Manager approach outlined in `ai-dev-manager-guide.md` at the project root.

## Directory Contents

- **sessions/**: Session logs from AI development sessions
  - Each file follows the format `session_YYYY-MM-DD.md`
  - Contains context, decisions, and progress from each session
  
- **test_plans/**: Detailed test plans for specific components
  - Currently includes GitHub Pages testing

## Using AI Dev Manager with ADRI

### Starting a New AI Development Session

When starting a new development session with an AI assistant:

1. **Begin by providing context**:
   ```
   Please review the ai-dev-manager-guide.md file and the ai_dev_manager directory to understand our development approach.
   ```

2. **Share the current session goals**:
   ```
   Today we'll be working on [specific feature/task], continuing from the previous session documented in ai_dev_manager/sessions/session_YYYY-MM-DD.md.
   ```

3. **Direct the AI to start in Continuity Manager Role**:
   ```
   Please start in Continuity Manager Role to review the current project state.
   ```

### Required Reading for AI Assistants

When starting a new session, the AI should review:

1. **ai-dev-manager-guide.md**: Methodology and roles
2. **ai_dev_manager/sessions/**: Previous session logs
3. **docs/PROJECT_STRUCTURE.md**: Project organization
4. **docs/TESTING.md**: Testing approach

### The Four Roles

The AI Dev Manager approach uses four distinct roles:

1. **Developer Role**: Implementation of functional code
   - Writing clean, efficient code that follows project standards
   - Implementing features according to specifications
   - Creating unit tests
   - Handling edge cases and error conditions

2. **Reviewer Role**: Critical analysis of code quality
   - Identifying code smells and inefficiencies
   - Ensuring adherence to project coding standards
   - Suggesting improvements and optimizations

3. **Technical Architect Role**: Documentation of design decisions
   - Updating technical documentation
   - Documenting design decisions and rationales
   - Ensuring architectural consistency

4. **Continuity Manager Role**: Knowledge transfer between sessions
   - Maintaining session briefs and progress logs
   - Documenting environment and context information
   - Documenting decisions and rationales

### Session Documentation

Each AI development session should produce:

1. **Session Log**: A comprehensive record of the session, stored in `ai_dev_manager/sessions/session_YYYY-MM-DD.md`
2. **Updated Documentation**: Any changes to architecture, testing approach, etc.
3. **Code Changes**: Implementation of features or bug fixes

### Maintenance of This Directory

This directory will be maintained during active development and removed when the project reaches a stable state. The contents provide context for future development sessions and serve as documentation of the development process.

## Guidelines for Humans

When working with AI assistants on ADRI:

1. **Begin with Context**: Start by directing the AI to review relevant files
2. **Be Clear About Roles**: Explicitly request role transitions when needed
3. **Document Sessions**: Ensure each session is documented following the template
4. **Follow Up**: Review session logs and ensure documentation is updated

## Example Session Flow

1. **Start**: Human asks AI to review project and take Continuity Manager role
2. **Planning**: AI reviews project state and proposes next steps
3. **Development**: AI transitions to Developer role to implement features
4. **Review**: AI transitions to Reviewer role to assess code quality
5. **Documentation**: AI transitions to Technical Architect role to update docs
6. **Continuity**: AI returns to Continuity Manager role to update session log
7. **Close**: Human reviews progress and confirms session documentation

## Templates

### Session Log Template

```markdown
# AI Dev Manager Session: YYYY-MM-DD

## Session Overview

**Session Focus:** [Brief description of session focus]

**Primary Tasks:**
1. [Task 1]
2. [Task 2]
3. [Task 3]

## Current Project State

[Brief description of the project state at the beginning of the session]

## Work Completed During This Session

### [Component/Feature 1]
- [Work done]
- [Decisions made]

### [Component/Feature 2]
- [Work done]
- [Decisions made]

## Next Steps

### 1. [Next Step 1] (Priority: High/Medium/Low)
- [Details]

### 2. [Next Step 2] (Priority: High/Medium/Low)
- [Details]

## Technical Decisions

### [Decision 1]
- **Decision:** [What was decided]
- **Rationale:** [Why it was decided]
- **Alternative Considered:** [What else was considered]
- **Why Rejected:** [Why alternative was rejected]

## Blockers and Questions

### Open Questions
1. [Question 1]
2. [Question 2]

### Resolved Questions
1. ✅ [Question 1] **[Answer]**
2. ✅ [Question 2] **[Answer]**

## Session Conclusion

[Brief summary of the session and what comes next]
