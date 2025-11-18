"""
Curl command generator - generates curl commands from HttpClient
"""

import json
import shlex
from typing import Dict, Any, Optional
from .http_client import HttpClient


class CurlGenerator:
    """Generates curl commands from HttpClient configuration"""
    
    def __init__(self, http_client: HttpClient):
        """
        Initialize curl generator
        
        Args:
            http_client: HttpClient instance with request configuration
        """
        self.http_client = http_client
    
    def generate(self) -> str:
        """
        Generate curl command from http_client configuration
        
        Returns:
            Complete curl command as string with line breaks
        """
        method = self.http_client.get_method()
        url = self.http_client.get_url()
        headers = self.http_client.get_headers()
        type, body = self.http_client.get_body()
        query_params = self.http_client.get_query_params()
        timeout = self.http_client.get_timeout()
        verify_ssl = self.http_client.get_ssl()
        
        # Start building curl command
        curl_parts = ["curl"]
        
        # Add method
        if method != "GET":
            curl_parts.append(f"-X {method}")
        
        # Add headers
        for key, value in headers.items():
            curl_parts.append(f"-H {shlex.quote(f'{key}: {value}')}")
        
        # Add body
        if body is not None:
            if type == 'json':
                # JSON body
                json_str = json.dumps(body, ensure_ascii=False)
                curl_parts.append(f"-d {shlex.quote(json_str)}")
            elif type == 'data':
                # Other body types
                if isinstance(body, dict):
                    # Form data
                    for key, value in body.items():
                        curl_parts.append(f"-d {shlex.quote(f'{key}={value}')}")
                elif isinstance(body, str):
                    # Text body
                    curl_parts.append(f"-d {shlex.quote(body)}")
        
        # Build final URL with query params
        final_url = url
        if query_params:
            query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
            final_url = f"{url}?{query_string}"
        
        curl_parts.append(shlex.quote(final_url))
        
        # Add timeout
        if timeout is not None:
            curl_parts.append(f"--max-time {timeout}")
        
        # Add SSL verification flag
        if not verify_ssl:
            curl_parts.append("-k")
        
        # Add verbose flag at the end
        curl_parts.append("-v")
        
        return " ".join(curl_parts)
    
    def print_curl(self):
        """Generate and print curl command"""
        curl_command = self.generate()
        print("\n" + "="*80)
        print("Generated cURL Command:")
        print("="*80)
        print(curl_command)
        print("="*80 + "\n")
