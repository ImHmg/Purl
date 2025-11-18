"""Tests for request processor"""

import pytest
import tempfile
import shutil
from pathlib import Path

from purl.processor import RequestProcessor


class TestRequestProcessor:
    """Test RequestProcessor class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def setup_test_env(self, temp_dir):
        """Setup test environment with config files"""
        # Create env directory
        env_dir = Path(temp_dir) / 'env'
        env_dir.mkdir()
        
        # Create environment config
        env_file = env_dir / 'test.properties'
        with open(env_file, 'w') as f:
            f.write("api_token=test_token_123\n")
            f.write("base_url=https://test.example.com\n")
            f.write("page_size=25\n")
        
        return temp_dir
    
    def test_process_simple_request(self, setup_test_env):
        """Test processing a simple request"""
        temp_dir = setup_test_env
        
        # Create request file
        request_file = Path(temp_dir) / 'request.yaml'
        with open(request_file, 'w') as f:
            f.write("""
Method: GET
Endpoint: https://example.com/api
Headers:
  Authorization: Bearer token123
""")
        
        processor = RequestProcessor(temp_dir)
        parsed = processor.process_request(str(request_file))
        
        assert parsed.spec.method == 'GET'
        assert parsed.resolved_endpoint == 'https://example.com/api'
        assert parsed.resolved_headers['Authorization'] == 'Bearer token123'
    
    def test_process_request_with_variables(self, setup_test_env):
        """Test processing request with variable substitution"""
        temp_dir = setup_test_env
        
        # Create request file
        request_file = Path(temp_dir) / 'request.yaml'
        with open(request_file, 'w') as f:
            f.write("""
Method: GET
Endpoint: ${base_url}/api
Headers:
  Authorization: Bearer ${api_token}
QueryParams:
  size: ${page_size}
""")
        
        processor = RequestProcessor(temp_dir)
        parsed = processor.process_request(str(request_file), env_names=['test'])
        
        assert parsed.resolved_endpoint == 'https://test.example.com/api'
        assert parsed.resolved_headers['Authorization'] == 'Bearer test_token_123'
        assert parsed.resolved_query_params['size'] == 25
    
    def test_process_request_with_define(self, setup_test_env):
        """Test processing request with Define section"""
        temp_dir = setup_test_env
        
        # Create request file
        request_file = Path(temp_dir) / 'request.yaml'
        with open(request_file, 'w') as f:
            f.write("""
Define:
  userId: user_123
  apiPath: /users/${userId}

Method: GET
Endpoint: ${base_url}${apiPath}
Headers:
  Authorization: Bearer ${api_token}
""")
        
        processor = RequestProcessor(temp_dir)
        parsed = processor.process_request(str(request_file), env_names=['test'])
        
        assert parsed.context_variables['userId'] == 'user_123'
        assert parsed.context_variables['apiPath'] == '/users/user_123'
        assert parsed.resolved_endpoint == 'https://test.example.com/users/user_123'
    
    def test_process_request_with_json_body(self, setup_test_env):
        """Test processing request with JSON body"""
        temp_dir = setup_test_env
        
        # Create request file
        request_file = Path(temp_dir) / 'request.yaml'
        with open(request_file, 'w') as f:
            f.write("""
Define:
  userEmail: test@example.com

Method: POST
Endpoint: ${base_url}/users
Headers:
  Content-Type: application/json
  Authorization: Bearer ${api_token}

JsonBody: |
  {
    "email": "${userEmail}",
    "name": "Test User"
  }
""")
        
        processor = RequestProcessor(temp_dir)
        parsed = processor.process_request(str(request_file), env_names=['test'])
        
        assert parsed.resolved_body['email'] == 'test@example.com'
        assert parsed.resolved_body['name'] == 'Test User'
    
    def test_process_request_with_form_params(self, setup_test_env):
        """Test processing request with form parameters"""
        temp_dir = setup_test_env
        
        # Create request file
        request_file = Path(temp_dir) / 'request.yaml'
        with open(request_file, 'w') as f:
            f.write("""
Define:
  username: testuser

Method: POST
Endpoint: ${base_url}/login

FormParams:
  username: ${username}
  password: testpass
  remember: true
""")
        
        processor = RequestProcessor(temp_dir)
        parsed = processor.process_request(str(request_file), env_names=['test'])
        
        assert parsed.resolved_body['username'] == 'testuser'
        assert parsed.resolved_body['password'] == 'testpass'
        assert parsed.resolved_body['remember'] is True
    
    def test_variable_priority_context_over_env(self, setup_test_env):
        """Test that context variables have priority over env variables"""
        temp_dir = setup_test_env
        
        # Create request file
        request_file = Path(temp_dir) / 'request.yaml'
        with open(request_file, 'w') as f:
            f.write("""
Define:
  api_token: context_token_override

Method: GET
Endpoint: ${base_url}/api
Headers:
  Authorization: Bearer ${api_token}
""")
        
        processor = RequestProcessor(temp_dir)
        parsed = processor.process_request(str(request_file), env_names=['test'])
        
        # Context variable should override env variable
        assert parsed.resolved_headers['Authorization'] == 'Bearer context_token_override'
    
    def test_multiple_env_configs_priority(self, setup_test_env):
        """Test priority with multiple environment configs"""
        temp_dir = setup_test_env
        
        # Create second env config
        env_dir = Path(temp_dir) / 'env'
        env_file2 = env_dir / 'override.properties'
        with open(env_file2, 'w') as f:
            f.write("api_token=override_token_456\n")
        
        # Create request file
        request_file = Path(temp_dir) / 'request.yaml'
        with open(request_file, 'w') as f:
            f.write("""
Method: GET
Endpoint: ${base_url}/api
Headers:
  Authorization: Bearer ${api_token}
""")
        
        processor = RequestProcessor(temp_dir)
        parsed = processor.process_request(str(request_file), env_names=['test', 'override'])
        
        # Last specified env (override) should have priority
        assert parsed.resolved_headers['Authorization'] == 'Bearer override_token_456'
        # But base_url from test should still be used
        assert parsed.resolved_endpoint == 'https://test.example.com/api'
    
    def test_format_request_log(self, setup_test_env):
        """Test formatting request log"""
        temp_dir = setup_test_env
        
        # Create request file
        request_file = Path(temp_dir) / 'request.yaml'
        with open(request_file, 'w') as f:
            f.write("""
Method: POST
Endpoint: ${base_url}/api
Headers:
  Content-Type: application/json

JsonBody: |
  {"test": "data"}
""")
        
        processor = RequestProcessor(temp_dir)
        parsed = processor.process_request(str(request_file), env_names=['test'])
        
        log = processor.format_request_log(parsed)
        
        assert 'POST' in log
        assert 'https://test.example.com/api' in log
        assert 'Content-Type' in log
        assert 'application/json' in log
    
    def test_process_request_with_path_params(self, setup_test_env):
        """Test processing request with path parameters"""
        temp_dir = setup_test_env
        
        # Create request file
        request_file = Path(temp_dir) / 'request.yaml'
        with open(request_file, 'w') as f:
            f.write("""
Define:
  userId: user123

Method: GET
Endpoint: ${base_url}/users/{userId}/posts/{postId}
PathParams:
  userId: ${userId}
  postId: post456
""")
        
        processor = RequestProcessor(temp_dir)
        parsed = processor.process_request(str(request_file), env_names=['test'])
        
        assert parsed.resolved_endpoint == 'https://test.example.com/users/user123/posts/post456'
