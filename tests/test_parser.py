"""Tests for YAML parser"""

import pytest
import tempfile
import os

from purl.parser import RequestParser
from purl.models import RequestSpec


class TestRequestParser:
    """Test RequestParser class"""
    
    def test_parse_minimal_request(self):
        """Test parsing minimal valid request"""
        data = {
            'Method': 'GET',
            'Endpoint': 'https://example.com/api'
        }
        
        spec = RequestParser.parse_dict(data)
        
        assert spec.method == 'GET'
        assert spec.endpoint == 'https://example.com/api'
        assert spec.define == {}
        assert spec.headers == {}
    
    def test_parse_full_request(self):
        """Test parsing request with all fields"""
        data = {
            'Method': 'POST',
            'Endpoint': 'https://example.com/api/users',
            'Define': {
                'userEmail': '${fake.email()}'
            },
            'Headers': {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ${token}'
            },
            'QueryParams': {
                'page': 1,
                'size': 10
            },
            'JsonBody': '{"email": "${userEmail}"}',
            'Options': {
                'insecure': True,
                'timeout': 30
            },
            'Captures': {
                'userId': '@body jsonpath $.id'
            },
            'Asserts': {
                'status is 200': '@status |==| 200'
            }
        }
        
        spec = RequestParser.parse_dict(data)
        
        assert spec.method == 'POST'
        assert spec.endpoint == 'https://example.com/api/users'
        assert 'userEmail' in spec.define
        assert spec.headers['Content-Type'] == 'application/json'
        assert spec.query_params['page'] == 1
        assert spec.json_body == '{"email": "${userEmail}"}'
        assert spec.options.insecure is True
        assert spec.options.timeout == 30
        assert 'userId' in spec.captures
        assert 'status is 200' in spec.asserts
    
    def test_parse_missing_method(self):
        """Test parsing request without Method field"""
        data = {
            'Endpoint': 'https://example.com/api'
        }
        
        with pytest.raises(ValueError, match="Missing required field: Method"):
            RequestParser.parse_dict(data)
    
    def test_parse_missing_endpoint(self):
        """Test parsing request without Endpoint field"""
        data = {
            'Method': 'GET'
        }
        
        with pytest.raises(ValueError, match="Missing required field: Endpoint"):
            RequestParser.parse_dict(data)
    
    def test_parse_file(self):
        """Test parsing from file"""
        yaml_content = """
Method: GET
Endpoint: https://example.com/api
Headers:
  Authorization: Bearer token123
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            spec = RequestParser.parse_file(temp_file)
            assert spec.method == 'GET'
            assert spec.endpoint == 'https://example.com/api'
            assert spec.headers['Authorization'] == 'Bearer token123'
        finally:
            os.unlink(temp_file)
    
    def test_parse_file_not_found(self):
        """Test parsing non-existent file"""
        with pytest.raises(FileNotFoundError):
            RequestParser.parse_file('nonexistent.yaml')
    
    def test_parse_form_params(self):
        """Test parsing request with FormParams"""
        data = {
            'Method': 'POST',
            'Endpoint': 'https://example.com/api',
            'FormParams': {
                'username': 'testuser',
                'password': 'testpass'
            }
        }
        
        spec = RequestParser.parse_dict(data)
        assert spec.form_params is not None
        assert spec.form_params['username'] == 'testuser'
        assert spec.get_body_type() == 'form'
    
    def test_parse_text_body(self):
        """Test parsing request with TextBody"""
        data = {
            'Method': 'POST',
            'Endpoint': 'https://example.com/api',
            'TextBody': 'Plain text content'
        }
        
        spec = RequestParser.parse_dict(data)
        assert spec.text_body == 'Plain text content'
        assert spec.get_body_type() == 'text'
    
    def test_parse_multipart_data(self):
        """Test parsing request with MultipartData"""
        data = {
            'Method': 'POST',
            'Endpoint': 'https://example.com/api',
            'MultipartData': {
                'file': 'path/to/file.txt',
                'description': 'Test file'
            }
        }
        
        spec = RequestParser.parse_dict(data)
        assert spec.multipart_data is not None
        assert spec.get_body_type() == 'multipart'
