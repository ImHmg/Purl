# HTML Report Feature for Purl Suite Runner

## Overview

The HTML report feature automatically generates comprehensive, light-themed HTML reports for suite executions. Reports include detailed information about requests, responses, assertions, captures, and row variables.

## Features

### Report Contents
- **Summary Statistics**
  - Total rows executed
  - Total requests made
  - Total assertions
  - Success/failed assertion counts
  - Failure rate percentage
  
- **Per-Row Details**
  - Row index
  - Row variables (from CSV data sources)
  
- **Per-Request Details**
  - Request file name
  - HTTP method and URL
  - Request headers (collapsible)
  - Request body (collapsible)
  - Response status code and time
  - Response headers (collapsible)
  - Response body (collapsible)
  - Assertions with pass/fail status
  - Captured variables
  - Error messages (if any)

### Styling
- Light theme using Bootstrap 5.3.8
- Compact, responsive design
- Color-coded status indicators:
  - ✓ Green for successful assertions
  - ✗ Red for failed assertions
  - Blue for informational badges
  - Yellow for warnings
- Collapsible sections for headers and bodies to keep report compact

## Configuration

### Report Path

You can specify a custom report path in your suite YAML file using the `ReportPath` field:

```yaml
Name: User Creation Suite
ReportPath: reports/user_creation_report.html  # Custom path

DataSources: ../data/create_users.csv

Configs:
  - dev

Requests:
  - ../requests/create_user.yaml
  - ../requests/get_user.yaml
```

### Path Resolution

1. **Custom Path (Relative)**: If `ReportPath` is specified and relative, it will be resolved relative to the working directory
   ```yaml
   ReportPath: reports/my_report.html
   # Resolves to: {working_dir}/reports/my_report.html
   ```

2. **Custom Path (Absolute)**: If `ReportPath` is specified and absolute, it will be used as-is
   ```yaml
   ReportPath: C:/reports/my_report.html
   # Uses: C:/reports/my_report.html
   ```

3. **Default Path**: If `ReportPath` is not specified, reports are stored in `.purl/reports/` with the format:
   ```
   {working_dir}/.purl/reports/{suite_name}_{timestamp}.html
   ```
   Example: `.purl/reports/user_creation_suite_20251123_164530.html`

## Usage

### Basic Suite Execution

```bash
purl -s samples/suites/user_creation_suite.yaml
```

This will:
1. Execute all requests in the suite
2. Generate an HTML report
3. Print the report path: `Suite report generated: {path}`

### With Custom Report Path

Create a suite file with `ReportPath`:

```yaml
Name: My Test Suite
ReportPath: test_results/my_report.html

Requests:
  - request1.yaml
  - request2.yaml
```

Run the suite:
```bash
purl -s my_suite.yaml
```

The report will be saved to `{working_dir}/test_results/my_report.html`

### With Data Sources

When using CSV data sources, each row is executed separately and shown in the report:

```yaml
Name: User Creation Suite
DataSources: data/users.csv

Requests:
  - create_user.yaml
```

The report will show:
- Row 1 with its variables
  - Request results for Row 1
- Row 2 with its variables
  - Request results for Row 2
- And so on...

## Report Structure

### Header Section
- Suite name
- Generation timestamp
- Summary statistics cards

### Results Section
For each data row:
- **Row Header**: Shows row number and variable count
- **Row Variables**: Displays all variables from the CSV row (if any)
- **Request Results**: For each request in the row:
  - Request details (method, URL, headers, body)
  - Response details (status, time, headers, body)
  - Assertions (with pass/fail indicators)
  - Captures (variable name and value)
  - Error messages (if request failed)

## Example Report Output

```
🧪 Purl Suite Report
Suite: User Creation Suite | Generated: 2025-11-23 16:45:30

[Statistics Cards]
Total Rows: 3
Total Requests: 6
Total Asserts: 12
Success Asserts: 10
Failed Asserts: 2
Failure Rate: 16.7%

📋 Row 1 - 3 variable(s)
[Row Variables]
username: john_doe
email: john@example.com
age: 25

Request #1: create_user.yaml
[Request Details]
POST https://api.example.com/users
✓ Status code is 201
✓ Response contains user_id
✗ Email format is valid (Expected: valid email, Got: invalid)

Request #2: get_user.yaml
[Request Details]
GET https://api.example.com/users/123
✓ Status code is 200
...
```

## Technical Details

### File Location
- Reporter class: `src/purl/reporters/html_reporter.py`
- Integration: `src/purl/suite_runner.py` (lines 60-64)

### Dependencies
- Bootstrap CSS: `src/purl/assets/bootstrap.css`
- Bootstrap JS: `src/purl/assets/bootstrap.js`

### Data Structure

The reporter receives `aggregated_results` with this structure:

```python
[
    {
        "row_index": 1,
        "variables": {"username": "john", "email": "john@example.com"},
        "requests": [
            {
                "status": "complete",
                "file": "/path/to/request.yaml",
                "asserts": {
                    "Status code is 200": {
                        "pass": True,
                        "actual": 200,
                        "expected": 200,
                        "op": "=="
                    },
                    "Has user_id": {
                        "pass": False,
                        "actual": None,
                        "expected": None,
                        "op": None
                    }
                },
                "captures": {
                    "user_id": "12345",
                    "username": "john_doe"
                },
                "request": {
                    "url": "https://api.example.com/users",
                    "headers": {...},
                    "json": {...}
                },
                "response": <Response object>,
                "request_spec": {...}
            }
        ]
    }
]
```

### Error Handling

If a request fails with an error status:
```python
{
    "status": "error",
    "message": "Connection timeout",
    "file": "/path/to/request.yaml"
}
```

The report will display an error message instead of request/response details.

## Customization

To customize the report appearance, modify:
- `src/purl/reporters/html_reporter.py` - Report generation logic
- CSS styles in the `_generate_html()` method
- Bootstrap theme variables in `src/purl/assets/bootstrap.css`

## Notes

- Reports are generated after all suite executions complete
- Large response bodies are automatically truncated in the display
- Collapsible sections help keep the report compact
- All HTML special characters are properly escaped
- Reports are self-contained (CSS/JS embedded)
