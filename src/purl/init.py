"""
Project initialization module for purl
"""

import os
from pathlib import Path
from typing import List

from .output import ColoredOutput
from .config import Config


SAMPLE_REQUEST_YAML = """# Sample GET Request
# Documentation: https://github.com/yourusername/purl

Define:
  userId: 1
  postId: 1

Method: GET
Endpoint: https://jsonplaceholder.typicode.com/posts/1

Headers:
  Accept: application/json
  User-Agent: purl/1.0

Captures:
  responseId: "@body jsonpath $.id"
  responseTitle: "@body jsonpath $.title"
  statusCode: "@status"

Asserts:
  "status code is 200": "@status |==| 200"
  "response has id": "@body jsonpath $.id"
  "response has title": "@body jsonpath $.title"

Options:
  timeout: 30
  insecure: false
"""

SAMPLE_POST_REQUEST_YAML = """# Sample POST Request
Define:
  title: Sample Post Title
  body: This is a sample post body
  userId: 1
  userEmail: "${fake.email()}"

Method: POST
Endpoint: https://jsonplaceholder.typicode.com/posts

Headers:
  Content-Type: application/json
  Accept: application/json
  X-Request-ID: "${fake.uuid4()}"

JsonBody: |
  {
    "title": "${title}",
    "body": "${body}",
    "userId": ${userId},
    "email": "${userEmail}"
  }

Captures:
  postId: "@body jsonpath $.id"
  createdAt: "@body jsonpath $.createdAt"
  statusCode: "@status"

Asserts:
  "status code is 201": "@status |==| 201"
  "response has id": "@body jsonpath $.id"
  "title matches": "@body jsonpath $.title |==| ${title}"

Options:
  timeout: 30
  insecure: false
"""

DEFAULT_PVARS = """# Project Variables
# These variables are available across all requests

# API Configuration
api_base_url: https://api.example.com
api_version: v1

# Authentication
api_key: your-api-key-here
auth_token: your-token-here

# Common Values
default_timeout: 30
retry_count: 3
"""

def get_default_pcfg() -> str:
    """Generate default pcfg.yaml content"""
    return f"""# purl configuration
# Path to configs directory (relative to project root)
configs_dir: {Config.DEFAULT_CONFIGS_DIR}
"""


def create_env_config(env_name: str) -> str:
    """Generate environment-specific configuration content"""
    configs = {
        'dev': """# Development Environment Configuration
api_base_url: https://dev-api.example.com
api_version: v1
environment: development
debug: true
timeout: 60
""",
        'uat': """# UAT Environment Configuration
api_base_url: https://uat-api.example.com
api_version: v1
environment: uat
debug: false
timeout: 30
""",
        'prod': """# Production Environment Configuration
api_base_url: https://api.example.com
api_version: v1
environment: production
debug: false
timeout: 30
"""
    }
    
    # Return specific config or generate generic one
    if env_name.lower() in configs:
        return configs[env_name.lower()]
    else:
        return f"""# {env_name.upper()} Environment Configuration
api_base_url: https://{env_name}-api.example.com
api_version: v1
environment: {env_name}
debug: false
timeout: 30
"""


def initialize_project(configs: List[str] = None):
    """
    Initialize purl project structure
    
    Args:
        configs: List of config names to create
    """
    current_dir = Path.cwd()
    
    ColoredOutput.header("Initializing purl project structure")
    print()
    
    # Create .purl directory
    purl_dir = current_dir / Config.PURL_DIR
    if not purl_dir.exists():
        purl_dir.mkdir(parents=True)
        ColoredOutput.success(f"✓ Created directory: {Config.PURL_DIR}/")
    else:
        ColoredOutput.info(f"  Directory already exists: {Config.PURL_DIR}/")
    
    # Create configs directory in current working directory
    configs_dir = current_dir / Config.DEFAULT_CONFIGS_DIR
    if not configs_dir.exists():
        configs_dir.mkdir(parents=True)
        ColoredOutput.success(f"✓ Created directory: {Config.DEFAULT_CONFIGS_DIR}/")
    else:
        ColoredOutput.info(f"  Directory already exists: {Config.DEFAULT_CONFIGS_DIR}/")
    
    # Create pcfg.properties file
    pcfg_file = purl_dir / Config.PCFG_FILE
    if not pcfg_file.exists():
        pcfg_file.write_text(get_default_pcfg(), encoding='utf-8')
        ColoredOutput.success(f"✓ Created file: {Config.PURL_DIR}/{Config.PCFG_FILE}")
    else:
        ColoredOutput.info(f"  File already exists: {Config.PURL_DIR}/{Config.PCFG_FILE}")
    
    # Create empty pvars.properties file
    pvars_file = purl_dir / Config.PVARS_FILE
    if not pvars_file.exists():
        pvars_file.write_text(DEFAULT_PVARS, encoding='utf-8')
        ColoredOutput.success(f"✓ Created file: {Config.PURL_DIR}/{Config.PVARS_FILE}")
    else:
        ColoredOutput.info(f"  File already exists: {Config.PURL_DIR}/{Config.PVARS_FILE}")
    
    # Create configs if specified
    if configs:
        for config_name in configs:
            config_file = configs_dir / config_name
            if not config_file.exists():
                config_content = create_env_config(config_name)
                config_file.write_text(config_content, encoding='utf-8')
                ColoredOutput.success(f"✓ Created config: {Config.DEFAULT_CONFIGS_DIR}/{config_name}")
            else:
                ColoredOutput.info(f"  Config already exists: {Config.DEFAULT_CONFIGS_DIR}/{config_name}")
    
    # Create sample request files
    sample_file = current_dir / 'sample.yaml'
    if not sample_file.exists():
        sample_file.write_text(SAMPLE_REQUEST_YAML, encoding='utf-8')
        ColoredOutput.success(f"✓ Created sample request: sample.yaml")
    else:
        ColoredOutput.info(f"  Sample file already exists: sample.yaml")
    
    sample_post_file = current_dir / 'sample-post.yaml'
    if not sample_post_file.exists():
        sample_post_file.write_text(SAMPLE_POST_REQUEST_YAML, encoding='utf-8')
        ColoredOutput.success(f"✓ Created sample POST request: sample-post.yaml")
    else:
        ColoredOutput.info(f"  Sample file already exists: sample-post.yaml")
    
    print()
    ColoredOutput.separator("=", 80, 'green')
    ColoredOutput.success("Project initialized successfully!")
    ColoredOutput.separator("=", 80, 'green')
    print()
    
    # Show next steps
    ColoredOutput.header("Next Steps:")
    print()
    print(f"  1. Edit {Config.PURL_DIR}/{Config.PVARS_FILE} to set your project variables")
    if configs:
        print(f"  2. Configure your configs in {Config.DEFAULT_CONFIGS_DIR}/")
        print(f"     Available: {', '.join(configs)}")
        print(f"  3. Run sample request:")
        print(f"     purl sample.yaml -c {configs[0]}")
    else:
        print(f"  2. Create configs in {Config.DEFAULT_CONFIGS_DIR}/")
        print(f"  3. Run sample request:")
        print(f"     purl sample.yaml")
    print()
