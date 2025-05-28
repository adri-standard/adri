# Contributing to the Agent Data Readiness Index (ADRI)

Thank you for your interest in contributing to ADRI! We welcome contributions from the community to help improve the standard, the toolkit, and the growing catalog of assessed public datasets. Let's work together to stop AI agents from flying blind!

There are multiple ways to get involved:

## Ways to Contribute

1.  **Methodology Improvements:** Help refine the ADRI assessment approach. Suggest new dimensions, refine scoring, provide case studies, or identify industry-specific needs. Open an issue to start a discussion.
2.  **Code Contributions:** Improve the `adri` Python package. Fix bugs, add features (like new connectors or dimensions), enhance integrations, improve performance, or write tests and documentation. Follow the process below.
3.  **Public Dataset Assessments:** Help build the Community Dataset Catalog! Assess commonly used public datasets using the `adri` tool and submit your results. See the specific process below.
4.  **Documentation & Examples:** Improve existing documentation (in the `docs/` directory), create new tutorials or usage examples (in the `examples/` or `notebooks/` directories), or write blog posts about ADRI.

## Code Contribution Process

1.  **Setup:** Follow the [Development Environment Setup](DEVELOPER.md#development-environment-setup) guide.
2.  **Find/Create an Issue:** Look for existing issues or open a new one to discuss your proposed change.
3.  **Fork & Branch:** Fork the repository and create a new branch for your feature or fix (e.g., `feature/new-connector` or `fix/report-bug`).
4.  **Develop:** Make your changes, adhering to the project's code style and standards (see [Code Style](DEVELOPER.md#code-style)). Ensure you add appropriate tests and update documentation.
5.  **Test:** Run tests locally (`pytest`) and ensure they pass. Check code quality (`black`, `isort`, `flake8`, `mypy`).
6.  **Commit:** Use Conventional Commit messages (e.g., `feat: add S3 connector`, `fix: correct completeness calculation`).
7.  **Pull Request (PR):** Push your branch to your fork and open a Pull Request against the main repository's `main` branch. Clearly describe your changes in the PR.
8.  **Review:** Engage in the code review process and address any feedback.
9.  **Merge:** Once approved, maintainers will merge your PR.

## Submitting Public Dataset Assessments

Contributing assessments of public datasets is crucial for building the Community Dataset Catalog.

1.  **Choose a Dataset:** Select a public dataset commonly used by AI agents (e.g., from Kaggle, Hugging Face Datasets, government portals). Prioritize datasets that are not yet in our `assessed_datasets/` directory or where existing assessments might be outdated.
2.  **Run Assessment:** Use the latest version of the `adri` tool to assess the dataset.
    ```bash
    # Example
    pip install adri --upgrade
    adri assess --source path/to/your/dataset.csv --output my_dataset_report
    ```
    This will generate `my_dataset_report.json` and `my_dataset_report.html`.
3.  **Prepare Submission:**
    *   **JSON Report:** Ensure the generated JSON report (`my_dataset_report.json`) includes the `adri_version` and `assessment_config` fields (this should happen automatically with recent versions).
    *   **Metadata:** Create a small `metadata.yaml` (or similar) file alongside the JSON report containing:
        *   `dataset_name`: Clear name of the dataset.
        *   `dataset_url`: Link to the dataset source.
        *   `dataset_description`: Brief description.
        *   `assessed_by`: Your GitHub username or name.
        *   `assessment_date`: Date of assessment (YYYY-MM-DD).
        *   `notes`: (Optional) Any relevant context or observations about the assessment or dataset.
4.  **Fork & Branch:** Fork the repository and create a new branch (e.g., `data/add-my-dataset-assessment`).
5.  **Add Files:** Place your `my_dataset_report.json` and `metadata.yaml` files within the `assessed_datasets/` directory. Please create a logical subdirectory structure if appropriate (e.g., `assessed_datasets/kaggle/my_dataset/`).
6.  **Pull Request (PR):** Push your branch and open a PR. Title it clearly (e.g., "Add assessment for My Dataset"). In the description, briefly mention the dataset and link to its source.
7.  **Review:** Maintainers will review the submission for completeness and validity. They may ask clarifying questions.
8.  **Merge:** Once approved, your assessment will be merged and potentially incorporated into the main Community Dataset Catalog visualization on the project website.

## Community Guidelines

*   Be respectful, constructive, and welcoming in all interactions (issues, PRs, discussions).
*   Clearly articulate your proposals or issues.
*   Adhere to the project's code of conduct (if one exists - consider adding one).

## Questions?

If you have questions about contributing, please open an issue or reach out to the maintainers.

Thank you for contributing!

## Purpose & Test Coverage

**Why this file exists**: Provides clear guidelines for community contributions to ADRI, fostering an open and collaborative development environment.

**Key responsibilities**:
- Outline contribution types and processes
- Guide code contribution workflow
- Explain public dataset assessment submission
- Define community guidelines and standards
- Encourage diverse forms of participation

**Test coverage**: This document's processes and guidelines should be verified by tests documented in [CONTRIBUTING_test_coverage.md](./test_coverage/CONTRIBUTING_test_coverage.md)
