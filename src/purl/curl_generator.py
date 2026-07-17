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
            Complete curl command as a multi-line string: 'curl <method> <url>'
            on the first line, followed by one flag per line, each continued
            with a trailing backslash (bash/zsh/git-bash line-continuation
            style, as used by browser "Copy as cURL" commands)
        """
        method = self.http_client.get_method()
        url = self.http_client.get_url()
        headers = self.http_client.get_headers()
        type, body = self.http_client.get_body()
        query_params = self.http_client.get_query_params()
        timeout = self.http_client.get_timeout()
        verify_ssl = self.http_client.get_ssl()
        cert = self.http_client.get_cert()

        # Build final URL with query params
        final_url = url
        if query_params:
            query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
            final_url = f"{url}?{query_string}"

        # First line: method + URL
        first_line_parts = ["curl"]
        if method != "GET":
            first_line_parts.append(f"-X {method}")
        first_line_parts.append(shlex.quote(final_url))

        # Remaining flags, one per line
        flag_lines = []

        for key, value in headers.items():
            flag_lines.append(f"-H {shlex.quote(f'{key}: {value}')}")

        if body is not None:
            if type == 'json':
                json_str = json.dumps(body, ensure_ascii=False)
                flag_lines.append(f"-d {shlex.quote(json_str)}")
            elif type == 'data':
                if isinstance(body, dict):
                    for key, value in body.items():
                        flag_lines.append(f"-d {shlex.quote(f'{key}={value}')}")
                elif isinstance(body, str):
                    flag_lines.append(f"-d {shlex.quote(body)}")

        if timeout is not None:
            flag_lines.append(f"--max-time {timeout}")

        # Client certificate for mTLS
        if cert is not None:
            if isinstance(cert, tuple):
                cert_file, key_file = cert
                flag_lines.append(f"--cert {shlex.quote(cert_file)}")
                flag_lines.append(f"--key {shlex.quote(key_file)}")
            else:
                flag_lines.append(f"--cert {shlex.quote(cert)}")

        # SSL verification flag / custom CA bundle
        if isinstance(verify_ssl, str):
            flag_lines.append(f"--cacert {shlex.quote(verify_ssl)}")
        elif not verify_ssl:
            flag_lines.append("-k")

        flag_lines.append("-v")

        lines = [" ".join(first_line_parts)] + flag_lines
        return " \\\n  ".join(lines)

    def print_curl(self):
        """Generate and print curl command"""
        curl_command = self.generate()
        print("\n" + "="*80)
        print("Generated cURL Command:")
        print("="*80)
        print(curl_command)
        print("="*80 + "\n")
