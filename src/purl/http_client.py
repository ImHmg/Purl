"""
HTTP client for executing requests
"""

import json
import requests
import time
import warnings
from typing import Dict, Any, Optional
from unittest.mock import Mock
from urllib3.exceptions import InsecureRequestWarning
from .args import PurlArgs

# Suppress SSL warnings when --insecure is used
warnings.filterwarnings('ignore', category=InsecureRequestWarning)


class HttpClient:
    """Executes HTTP requests based on parsed YAML data"""
    
    def __init__(self, request_data: Dict[str, Any]):
        """Initialize HTTP client"""
        self.request_data = request_data
        self.elapsed_time = 0
        self.args = PurlArgs()
    
    def get_method(self) -> str:
        """Get HTTP method from request data"""
        return self.request_data.get('Method', 'GET').upper()
    
    def get_url(self) -> str:
        """Get URL from request data"""
        return self.request_data.get('Endpoint', '')
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers from request data"""
        headers = self.request_data.get('Headers', {})
        if 'JsonBody' in self.request_data:
            headers['Content-Type'] = 'application/json'
        return headers
    
    def get_body(self) -> Optional[Any]:
        """Get request body from request data"""
        # Check for different body types
        if 'Body' in self.request_data:
            return 'data', self.request_data['Body']
        elif 'JsonBody' in self.request_data:
            return 'json', self.request_data['JsonBody']
        elif 'FormBody' in self.request_data:
            return 'data', self.request_data['FormBody']
        elif 'TextBody' in self.request_data:
            return 'data', self.request_data['TextBody']
        elif 'MultipartBody' in self.request_data:
            return 'data',self.request_data['MultipartBody']
        return 'data', None

    def get_body_type(self) -> Optional[Any]:
        """Get request body from request data"""
        # Check for different body types
        if 'Body' in self.request_data:
            return 'Body'
        elif 'JsonBody' in self.request_data:
            return 'JsonBody'
        elif 'FormBody' in self.request_data:
            return 'FormBody'
        elif 'TextBody' in self.request_data:
            return 'TextBody'
        elif 'MultipartBody' in self.request_data:
            return 'MultipartBody'
        return 'Body'
    
    def get_query_params(self) -> Dict[str, str]:
        """Get query parameters from request data"""
        return self.request_data.get('QueryParams', {})
    
    def get_timeout(self) -> Optional[int]:
        """Get timeout from request data"""
        return self.request_data.get('Options', {}).get('timeout') or self.args.timeout or None
    
    def get_ssl(self) -> Optional[bool]:
        """Get SSL from request data"""
        if self.args.insecure:
            return False
        
        if self.request_data.get('Options', {}).get('insecure') == False:
            return False

        return True
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute HTTP request based on parsed YAML data
        
        Returns:
            Response data dictionary
        """
        method = self.get_method()
        url = self.get_url()
        headers = self.get_headers()
        type, body = self.get_body()
        query_params = self.get_query_params()
        timeout = self.get_timeout()
        verify_ssl = self.get_ssl()

        # Prepare request kwargs
        request_kwargs = {
            'url': url,
            'headers': headers,
            'params': query_params,
            type : body,
            'verify': verify_ssl
        }
        
        # Add timeout if specified
        if timeout is not None:
            request_kwargs['timeout'] = timeout
        
        # Execute request and track time
        start_time = time.time()
        self.response = requests.request(method, **request_kwargs)
        end_time = time.time()
        
        # Calculate elapsed time in milliseconds
        self.elapsed_time = (end_time - start_time) * 1000
        
        return self.response

