# Purl - API Testing Tool

A powerful HTTP request testing tool with YAML configuration, variable substitution, fake data generation, and Python scripting capabilities.

## 🚀 Features

- **YAML Configuration** - Define HTTP requests in simple, readable YAML files
- **Variable Substitution** - Use variables from configs, properties files, and command-line
- **Fake Data Generation** - Built-in Faker integration for generating realistic test data
- **Response Capture** - Extract and store values from responses using JSONPath
- **Assertions** - Validate responses with simple assertion syntax
- **PreExec/PostExec Scripts** - Execute Python code before and after requests
- **Multiple Environments** - Switch between dev, UAT, prod with configuration files
- **cURL Generation** - Generate cURL commands without executing requests
- **SSL Control** - Enable/disable SSL verification per request or globally
- **Timeout Management** - Set timeouts globally or per request

## 📦 Installation

```bash
# Install from source
pip install -e .

# Or install dependencies
pip install -r requirements.txt
```

## 🎯 Quick Start

### 1. Initialize Project

```bash
# Basic init
purl --init

# Init and create a dev config + sample requests
purl --init -c dev
```

This creates the project structure in the current directory:
```
./
├── .purl/
│   ├── pcfg.properties   # purl configuration
│   └── pvars.properties  # Persistent variables storage
├── configs/
│   └── dev.properties    # Created when you pass -c dev
├── sample.yaml           # Sample GET request
└── sample-post.yaml      # Sample POST request
```

### 2. Create Configuration File

If you didn't create it during init, create `configs/dev.properties`:
```properties
base_url=http://localhost:3000
authorization_token=Bearer dev_auth_token_12345
api_version=v1
default_timeout=30
```

### 3. Create Request File

Create `my_request.yaml`:
```yaml
Method: GET
Endpoint: ${base_url}/api/${api_version}/users

Headers:
  Authorization: ${authorization_token}
  Accept: application/json

Options:
  timeout: ${default_timeout}
```

### 4. Execute Request

```bash
purl my_request.yaml -c dev
```

## 📖 Usage

### Command-Line Options

```bash
# Basic execution
purl request.yaml

# With configuration
purl request.yaml -c dev

# Multiple configs (later configs override earlier ones)
purl request.yaml -c dev -c local

# Override variables
purl request.yaml -c dev --var user_id=123 --var email=test@example.com

# Set timeout
purl request.yaml -c dev --timeout 60

# Disable SSL verification
purl request.yaml -c dev --insecure

# Generate cURL command (don't execute)
purl request.yaml -c dev --generate

# Enable debug mode
purl request.yaml -c dev --debug

# Set working directory
purl request.yaml -c dev --working-dir /path/to/project

# Show version
purl --version

# Show help
purl --help
```

## 📝 Request File Format

### Complete Example

```yaml
# Define local variables (optional)
Define:
  user_id: "12345"
  request_id: "${fake.uuid4()}"

# PreExec script (optional) - runs after Define section
PreExec: |
  # Generate dynamic data
  username = faker.user_name()
  set_var('dynamic_username', username)
  print(f"Generated username: {username}")

# HTTP Method (GET, POST, PUT, DELETE, PATCH, etc.)
Method: POST

# Endpoint URL
Endpoint: ${base_url}/api/${api_version}/users/${user_id}

# Headers
Headers:
  Authorization: ${authorization_token}
  Content-Type: application/json
  X-Request-ID: ${request_id}

# Query Parameters
QueryParams:
  page: 1
  limit: 10
  sort: created_at
  order: desc

# JSON Body
JsonBody: |
  {
    "name": "${fake.name()}",
    "email": "${fake.email()}",
    "age": 28
  }

# Alternative: Form Body
# FormBody:
#   username: testuser
#   password: secret123

# Alternative: Text Body
# TextBody: |
#   Plain text content here

# Options
Options:
  timeout: 30
  insecure: false

# Capture values from response
Captures:
  user_id: "@body jsonpath $.id"
  user_email: "@body jsonpath $.email"
  status_code: "@status"

# Assert response values
Asserts:
  "status code is 201": "@status |==| 201"
  "response has user id": "@body jsonpath $.id"
  "email is not null": "@body jsonpath $.email"

# PostExec script (optional) - runs after everything
PostExec: |
  # Access captured variables
  user_id = get_var('user_id')
  print(f"Created user with ID: {user_id}")
```

### Request Components

#### Method
```yaml
Method: GET  # GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
```

#### Endpoint
```yaml
Endpoint: ${base_url}/api/${api_version}/users/${user_id}
```

#### Headers
```yaml
Headers:
  Authorization: Bearer ${auth_token}
  Content-Type: application/json
  Accept: application/json
  X-Custom-Header: custom-value
```

#### Query Parameters
```yaml
QueryParams:
  page: 1
  limit: 10
  sort: created_at
  filter: active
```

#### Body Types

**JSON Body:**
```yaml
JsonBody: |
  {
    "name": "${fake.name()}",
    "email": "${fake.email()}"
  }
```

**Form Body:**
```yaml
FormBody:
  username: testuser
  password: secret123
  remember_me: true
```

**Text Body:**
```yaml
TextBody: |
  Plain text content
  Multiple lines supported
  Variables: ${variable_name}
```

#### Options
```yaml
Options:
  timeout: 30        # Request timeout in seconds
  insecure: false    # Disable SSL verification (true/false)
```

## 🔧 Variable System

### Variable Priority (Highest to Lowest)

1. **Command-line variables** - `--var key=value`
2. **Config files** - Later configs override earlier ones
3. **Persistent variables** - `pvars.properties`
4. **Define section** - In request file

### Using Variables

```yaml
# Reference variables with ${variable_name}
Endpoint: ${base_url}/api/${api_version}/users/${user_id}

# Variables can reference other variables
Define:
  full_url: ${base_url}/api/${api_version}
  user_endpoint: ${full_url}/users
```

### Faker Integration

Generate fake data using `${fake.method_name()}`:

```yaml
JsonBody: |
  {
    "name": "${fake.name()}",
    "email": "${fake.email()}",
    "phone": "${fake.phone_number()}",
    "address": "${fake.address()}",
    "uuid": "${fake.uuid4()}",
    "date": "${fake.iso8601()}",
    "company": "${fake.company()}",
    "url": "${fake.url()}",
    "text": "${fake.text()}",
    "username": "${fake.user_name()}",
    "password": "${fake.password()}",
    "city": "${fake.city()}",
    "state": "${fake.state()}",
    "zipcode": "${fake.zipcode()}",
    "country": "${fake.country()}",
    "street_address": "${fake.street_address()}",
    "image_url": "${fake.image_url()}"
  }
```

See [Faker documentation](https://faker.readthedocs.io/) for all available methods.

## 🎭 Captures and Assertions

### Captures

Extract values from responses:

```yaml
Captures:
  user_id: "@body jsonpath $.id"
  user_email: "@body jsonpath $.email"
  user_name: "@body jsonpath $.name"
  status_code: "@status"
  response_time: "@time"
```

Captured values are stored as variables and can be used in subsequent requests or PostExec scripts.

### Assertions

Validate responses:

```yaml
Asserts:
  "status code is 200": "@status |==| 200"
  "response has user id": "@body jsonpath $.id"
  "email matches": "@body jsonpath $.email |==| ${expected_email}"
  "name is not null": "@body jsonpath $.name"
```

## 🐍 Scripting with PreExec and PostExec

### Available Functions

- `set_var(key, value)` - Store a variable in pvars (persistent)
- `get_var(key)` - Retrieve a variable value
- `faker` - Access to Faker instance
- `spec` - The parsed YAML specification
- `json` - JSON module
- `re` - Regular expressions module

### PreExec Example

Runs after Define section, before request execution:

```yaml
PreExec: |
  # Generate dynamic data
  username = faker.user_name()
  email = faker.email()
  
  # Store for use in request
  set_var('test_username', username)
  set_var('test_email', email)
  
  # Generate unique transaction ID
  import time
  txn_id = f"TXN-{int(time.time())}-{faker.random_number(digits=6)}"
  set_var('transaction_id', txn_id)
  
  # Read existing variables
  base_url = get_var('base_url')
  print(f"Using base URL: {base_url}")
  print(f"Generated username: {username}")
```

### PostExec Example

Runs after request execution and captures:

```yaml
PostExec: |
  # Get captured values
  user_id = get_var('user_id')
  user_email = get_var('user_email')
  status_code = get_var('status_code')
  
  # Conditional logic
  if status_code == '201':
      print(f"✓ User created: {user_id}")
      set_var('last_created_user', user_id)
  else:
      print(f"✗ Failed with status: {status_code}")
  
  # Data transformation
  import json
  summary = {
      'user_id': user_id,
      'email': user_email,
      'timestamp': faker.iso8601()
  }
  set_var('execution_summary', json.dumps(summary))
  
  print(f"Execution completed for user: {user_email}")
```

## 📂 Project Structure

```
your-project/
├── .purl/
│   ├── configs/
│   │   ├── dev.properties
│   │   ├── uat.properties
│   │   └── prod.properties
│   └── pvars.properties
├── requests/
│   ├── users/
│   │   ├── create_user.yaml
│   │   ├── get_user.yaml
│   │   └── update_user.yaml
│   └── auth/
│       ├── login.yaml
│       └── logout.yaml
└── README.md
```

## 📚 Examples

See the `samples/` directory for complete examples:

- `01_get_with_query_and_path.yaml` - GET request with query and path parameters
- `02_post_with_json_body.yaml` - POST request with JSON body
- `03_post_with_form_params.yaml` - POST request with form parameters
- `04_post_with_text_body.yaml` - POST request with text body
- `05_with_preexec_postexec.yaml` - Request with PreExec and PostExec scripts

### Running Examples

```bash
# Run with dev config
purl samples/01_get_with_query_and_path.yaml -c dev

# Run with variable override
purl samples/01_get_with_query_and_path.yaml -c dev --var user_id=999

# Generate cURL command
purl samples/02_post_with_json_body.yaml -c dev --generate

# Run with custom timeout
purl samples/03_post_with_form_params.yaml -c dev --timeout 60
```

## 🔐 Environment Configurations

### Development (dev.properties)
```properties
base_url=http://localhost:3000
authorization_token=Bearer dev_auth_token
api_version=v1
default_timeout=30
```

### UAT (uat.properties)
```properties
base_url=https://uat-api.example.com
authorization_token=Bearer uat_auth_token
api_version=v1
default_timeout=45
```

### Production (prod.properties)
```properties
base_url=https://api.example.com
authorization_token=Bearer prod_auth_token
api_version=v1
default_timeout=60
```

## 🛠️ Advanced Features

### Generate cURL Commands

```bash
purl request.yaml -c dev --generate
```

Output:
```bash
curl -H 'Authorization: Bearer token' -H 'Content-Type: application/json' -d '{"name":"John"}' 'http://localhost:3000/api/v1/users' --max-time 30 -v
```

### Multiple Configurations

```bash
# Later configs override earlier ones
purl request.yaml -c dev -c local-overrides
```

### Variable Override

```bash
# Override any variable from command line
purl request.yaml -c dev --var user_id=123 --var email=test@example.com
```

### Disable SSL Verification

```bash
# Globally
purl request.yaml -c dev --insecure

# Per request in Options section
Options:
  insecure: true
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🔗 Links

- [Faker Documentation](https://faker.readthedocs.io/)
- [JSONPath Documentation](https://goessner.net/articles/JsonPath/)
- [YAML Syntax](https://yaml.org/)

## 💡 Tips

1. **Use Define section** for request-specific variables
2. **Use configs** for environment-specific values
3. **Use pvars** for values that need to persist across requests
4. **Use PreExec** to generate dynamic test data
5. **Use PostExec** to validate and store response data
6. **Use Captures** to extract values for later use
7. **Use Asserts** to validate responses automatically
8. **Use --generate** to debug requests without executing them

## 🐛 Troubleshooting

### SSL Certificate Errors
```bash
# Disable SSL verification
purl request.yaml -c dev --insecure
```

### Timeout Issues
```bash
# Increase timeout
purl request.yaml -c dev --timeout 120
```

### Variable Not Found
- Check variable priority: Define > CLI > Configs > pvars
- Verify config file exists in `.purl/configs/`
- Check variable name spelling and case sensitivity

### Debug Mode
```bash
# Enable debug output
purl request.yaml -c dev --debug
```
