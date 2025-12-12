# SonarQube Configuration

This directory contains the SonarQube configuration for the Smart Heating project.

## Files

- `sonar-project.properties` - Main SonarQube configuration file

## Configuration Details

### Test File Exclusions

Test files are excluded from code quality analysis to focus on production code quality. The following patterns are excluded:

- `tests/**/*` - All test files
- `**/test_*.py` - Python test files
- `**/*_test.py` - Alternative test naming pattern
- `**/conftest.py` - pytest configuration
- `tests/e2e/**` - E2E test files

### Coverage

Test coverage is still collected and reported from test files, but code quality issues (complexity, code smells, etc.) are only reported for production code in the `smart_heating/` directory.

## Usage

### With SonarQube CLI

```bash
# The sonar-project.properties file will be automatically detected
sonar-scanner
```

### With GitHub Actions

The configuration is automatically picked up by the SonarQube GitHub Action when it runs.

## Key Settings

- **Project Key**: `TheFlexican_smart-heating`
- **Organization**: `theflexican`
- **Source Directory**: `smart_heating/`
- **Test Directory**: `tests/`
- **Python Version**: 3.13
- **Coverage Report**: `coverage.xml`

## Why Exclude Tests?

Test files often have different quality standards than production code:

- Tests may have higher cognitive complexity
- Mock/fixture setup code may trigger false positives
- Test-specific patterns may not follow production code standards
- We want to focus quality metrics on code that runs in production

Coverage metrics from tests are still reported to ensure production code is well-tested.

## VS Code SonarLint Extension Configuration

For local development with the SonarLint VS Code extension, add the following to your `.vscode/settings.json` (this file is gitignored and user-specific):

```json
{
    "sonarlint.connectedMode.project": {
        "connectionId": "theflexican",
        "projectKey": "TheFlexican_smart-heating"
    },
    "sonarlint.rules": {
        "python:S7503": {
            "level": "off"
        },
        "python:S1244": {
            "level": "off"
        },
        "python:S7493": {
            "level": "off"
        }
    },
    "sonarlint.testFilePattern": "**/{test_*,*_test,*Test*,*Spec*}.py",
    "sonarlint.disableTelemetry": true
}
```

### Disabled Rules Explanation

- **S7503**: "Use asynchronous features or remove async keyword" - Disabled for test fixtures that are async but may not await
- **S1244**: "Do not perform equality checks with floating point values" - Disabled as we use pytest.approx for float comparisons
- **S7493**: "Use asynchronous file API" - Disabled as tests may use synchronous file I/O for simplicity

### Test File Pattern

The `sonarlint.testFilePattern` setting tells SonarLint to apply different rules to test files. This pattern matches:
- `test_*.py` - Standard pytest naming
- `*_test.py` - Alternative test naming
- `*Test*.py` - Test classes
- `*Spec*.py` - Spec files (e2e tests)
