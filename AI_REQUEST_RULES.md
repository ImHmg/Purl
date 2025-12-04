# AI Request & Suite Authoring Guide

Use this guide whenever you need to convert a cURL command or a natural-language request description into runnable Purl request files **or** multi-step suites. Everything required is contained here so GPT can generate ready-to-run assets without extra context. Treat all paths as relative to the user’s project root.

## 1. Workspace & Folder Rules

1. **Project layout** – Store request YAML files and supporting assets (CSV data, payload templates, etc.) anywhere inside the user’s repository. Folder names like `requests/` or `samples/` are only examples—mirror the structure the user prefers.
2. **Execution context** – Run Purl from the project root. Always document the exact command with the correct relative path to the file (for example, `purl requests/create_user.yaml -c dev`).
3. **Config locations** – Purl reads environment configs from a configurable directory. By default it is `./configs`. Users can override this by creating `.purl/pcfg.properties` with `configs_dir=<relative_path>`. Whenever someone asks for a new config, create `<name>.properties` within the active configs directory.
4. **Config contents** – Configs are simple key/value files. Common entries include:
   ```properties
   base_url=https://dev-api.example.com
   authorization_token=Bearer dev_token_123
   api_version=v1
   default_timeout=30
   email_sender=no-reply@example.com
   ```
5. **Root-only assumptions** – Never hardcode absolute paths. Always reference files relative to the directory where the Purl command will run.

## 2. Request File Blueprint (No Suites)

Build each request YAML using the sections below (omit sections that don’t apply):

1. **Comment header & usage** – Describe the request and show the run command:
   ```yaml
   # Creates a user profile using environment config and CLI overrides
   # Usage: purl requests/create_user.yaml -c dev --var user_id=123
   ```
2. **Define** – Set per-request defaults and derived values:
   ```yaml
   Define:
     user_id: "12345"
     page_number: "1"
     request_id: "${fake.uuid4()}"
   ```
3. **Method / Endpoint / Status** – Copy these directly from the source information, swapping the host for `${base_url}` and reusing `${api_version}` when available:
   ```yaml
   Method: POST
   Endpoint: ${base_url}/api/${api_version}/users/${user_id}
   Status: 201
   ```
4. **QueryParams** – Expand query strings into a YAML map and keep placeholders for dynamic values:
   ```yaml
   QueryParams:
     page: ${page_number}
     limit: ${page_size}
     sort: created_at
     order: desc
   ```
5. **Headers** – Translate every header from the source request, replacing secrets with variables defined in configs or Define:
   ```yaml
   Headers:
     Authorization: ${authorization_token}
     Accept: application/json
     Content-Type: application/json
     X-Request-ID: ${request_id}
   ```
6. **Body** – Choose the block type that matches the payload:
   - `JsonBody: |` for JSON
   - `FormBody:` for form submissions (`application/x-www-form-urlencoded` or multipart form data)
   - `TextBody: |` for raw text
   - `FileBody:` for file uploads

   Example JSON body:
   ```yaml
   JsonBody: |
     {
       "id": "${user_id}",
       "name": "${user_name}",
       "email": "${user_email}",
       "preferences": {
         "newsletter": "${newsletter}",
         "locale": "${locale}"
       }
     }
   ```
7. **Captures** – Store response values needed later (see §3 for detailed rules):
   ```yaml
   Captures:
     created_user_id: "@body jsonpath $.id"
     created_user_email: "@body jsonpath $.email"
     status_code: "@status"
     response_time: "@time"
   ```
8. **Asserts** – Validate the response using the operators listed in §4. When the request already specifies a `Status:` value, Purl automatically checks it, so you do **not** need to add a duplicate assertion for that status code.
9. **Options** – Override per-request behavior only when needed:
   ```yaml
   Options:
     timeout: ${default_timeout}
     insecure: false
   ```
10. **PreExec / PostExec** – Include scripts only when the scenario requires advanced setup or teardown (see §6).

## 3. Capture Rules

- Captures are key-value mappings under the `Captures:` section.
- Values are expressions that extract response data (JSONPath, headers, status, response time, etc.).
- Name captures after their purpose (`created_user_id`, `status_code`, `response_time`).
- Common capture helpers:
  - `@body jsonpath $.field.path`
  - `@headers['Header-Name']`
  - `@status`
  - `@time` (response time in ms)
- Capture every value that will be reused across requests or scripts.

Example:
```yaml
Captures:
  created_user_id: "@body jsonpath $.id"
  access_token: "@body jsonpath $.tokens.access"
  status_code: "@status"
  response_time: "@time"
```

## 4. Assertion Rules

- Assertions live under the `Asserts:` section as `"label": "expression"` pairs.
- Supported operators: `|==|`, `|!=|`, `|>|`, `|<|`, `|contains|`, `|!contains|`.
- For non-null checks, omit an operator (e.g., `"has user id": "@body jsonpath $.id"`).
- Labels should describe the expected behavior so failures are actionable.
- Examples:
  ```yaml
  Asserts:
    "status code is 200": "@status |==| 200"
    "email matches payload": "@body jsonpath $.email |==| ${user_email}"
    "response time < 2s": "@time |<| 2000"
    "message mentions success": "@body jsonpath $.message |contains| success"
    "has user id": "@body jsonpath $.id"
  ```

## 5. Faker Usage

- **Inline placeholders** – Use `${fake.<method>()}` anywhere a literal would appear (e.g., `${fake.name()}`, `${fake.email()}`, `${fake.uuid4()}`, `${fake.phone_number()}`, `${fake.iso8601()}`).
- **Script usage** – Inside PreExec/PostExec, call the injected `faker` object and store values with `set_var()` so they can be referenced in the request body, headers, or future requests:
  ```python
  username = faker.user_name()
  email = faker.email()
  set_var('dynamic_username', username)
  set_var('dynamic_email', email)
  ```
- **Best practices** – Use faker for any data that should look realistic yet change every run (emails, transaction IDs, addresses, phone numbers).

## 6. PreExec & PostExec Scripts

- **PreExec** – Runs after Define and before the HTTP call. Use it for data generation, derived values, or logging:
  ```yaml
  PreExec: |
    print("PreExec started")
    txn_id = f"TXN-{faker.random_number(digits=6)}"
    set_var('transaction_id', txn_id)
    set_var('dynamic_email', faker.email())
  ```
- **PostExec** – Runs after captures are stored. Use it to inspect results, make decisions, or persist data:
  ```yaml
  PostExec: |
    status_code = get_var('status_code')
    user_id = get_var('created_user_id')
    if status_code == '201':
        print(f"✓ User created: {user_id}")
        set_var('last_created_user', user_id)
    else:
        print(f"✗ Creation failed with status {status_code}")
  ```
- **Safety tips** – Keep scripts idempotent, avoid network calls, and provide clear logging so issues are easy to trace.

## 7. Run Command Cheat Sheet

Always publish runnable commands from the project root. Replace `<path_to_request>` with the real relative path.

```bash
# Basic run
purl <path_to_request>.yaml -c dev

# Multiple configs (later overrides earlier)
purl <path_to_request>.yaml -c dev -c local-overrides

# Override variables at runtime
purl <path_to_request>.yaml -c dev --var user_id=123 --var email=test@example.com

# Customize timeout or SSL settings
purl <path_to_request>.yaml -c dev --timeout 60 --insecure

# Generate cURL without executing
purl <path_to_request>.yaml -c dev --generate

# Enable verbose debug output
purl <path_to_request>.yaml -c dev --debug

# Specify a different working directory
purl <path_to_request>.yaml -c dev --working-dir ./path/to/project

# Show help or version
purl --help
purl --version
```

## 8. Workflow: From cURL or Description to YAML

1. **Parse the source** – Identify method, endpoint, headers, query params, payload, and expected response details from the cURL or textual description.
2. **Normalize the endpoint** – Swap the host/scheme for `${base_url}` and convert dynamic segments into `${snake_case}` variables defined in `Define` or sourced from configs/data files.
3. **Design variables** – Decide which values belong in configs (shared secrets), Define (per-request defaults), or CSV data files (when iterating over rows).
4. **Translate payloads** – Reproduce JSON/form/text bodies exactly, inserting `${variables}` where dynamic data is required.
5. **Plan captures** – Determine the response fields needed later and add capture entries for them, including status code and response time.
6. **Add assertions** – Cover both HTTP status and critical response properties using the expressions from §3.
7. **Consider scripts** – Add PreExec/PostExec only if the scenario needs faker data generation, complex transformations, or persistence of results.
8. **Document the command** – Ensure the header comment shows precisely how to run the request with any required configs or variable overrides.

Following this guide ensures AI-generated request files stand on their own, honor configuration rules, and can be executed immediately on any user’s machine.

## 9. Suite Authoring Blueprint

Create a suite when multiple request files must run together while sharing configs, variables, or CSV-driven rows. The folder `samples/suites/` contains working references such as `user_creation_suite.yaml`, `user_listing_suite.yaml`, and `example_with_report.yaml`—mirror their style.

Include the sections below (omit ones that do not apply). Keep key names in TitleCase exactly as shown so the suite runner can parse them.

1. **Name** – Human-friendly label displayed in logs and reports.
2. **ReportPath** *(optional)* – Relative or absolute path for the HTML summary. If omitted, the report goes to `.purl/reports/{suite_name}_{timestamp}.html`.
3. **DataSources** – Path (string) or list containing a single CSV file that provides per-row variables. Each header becomes a variable for that run. Example:
   ```yaml
   DataSources: ../data/create_users.csv
   ```
4. **Configs** – Ordered list of config names. Entries are appended in front of CLI `-c` values, so later configs override earlier ones.
5. **Vars** – Static key/value pairs pushed into the variable context before any requests run. Use string values only.
6. **Requests** – Ordered list of request file paths (relative paths resolve from the suite file’s directory). Requests execute sequentially for every CSV row.
7. **Options** – Per-suite overrides such as `timeout` or `insecure`. They serve as defaults for every request unless the CLI already set them.

Example suite:

```yaml
Name: User Creation Suite
ReportPath: reports/example_suite_report.html
DataSources: ../data/create_users.csv
Configs:
  - dev
Vars:
  api_version: v1
  client_version: 1.0.0
Requests:
  - ../requests/create_user.yaml
  - ../requests/get_user.yaml
Options:
  timeout: 30
```

## 10. Linking Requests, DataSources, and Vars

1. **Request linking**
   - Suites run each listed request in order. Captures defined inside a request are written to the global variable store (`pvars`) and become available to all following requests in the same execution.
   - Reference earlier captures by name just like any `${variable}` placeholder (e.g., capture `created_user_id` in `create_user.yaml`, then use `${created_user_id}` inside `get_user.yaml`).
   - Keep capture names unique enough to avoid accidental reuse between suites.

2. **DataSources → Vars**
   - When `DataSources` points to a CSV, each header/value pair in a row is merged into the variables dictionary (as strings) before the first request runs for that row.
   - CSV values override Suite `Vars`, which override config values, which override persisted `pvars`.
   - Empty cells become empty strings; provide defaults via Suite `Vars` if a column can be blank.

3. **Suite Vars best practices**
   - Use Suite `Vars` for constants shared across all rows (API version, feature flags, etc.).
   - Names must be valid identifiers (letters, numbers, underscore) so they can appear in `${var_name}` placeholders.
   - Avoid storing secrets here—prefer configs when values must be hidden outside version control.

4. **Data-driven overrides**
   - If a CSV column matches a variable already defined in Suite `Vars` or configs, the CSV value wins for that row.
   - Combine CSV rows with faker-driven Captures to build multi-step flows (e.g., CSV supplies `email_domain`, PreExec builds `email`, captures store `user_id`).

5. **Run command for suites**
   ```bash
   purl -s samples/suites/user_creation_suite.yaml -c dev
   ```
   Add `--var` overrides or additional `-c` flags exactly like single-request runs.

Document every suite so GPT knows which CSVs, configs, and requests belong together. Provide explicit file paths and commands in prompts so generated suites stay runnable without manual fixes.
