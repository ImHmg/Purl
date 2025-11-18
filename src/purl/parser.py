"""
YAML request file parser
"""

import yaml
from pathlib import Path
from typing import Dict, Any

from .models import RequestSpec, RequestOptions


class RequestParser:
    """Parses YAML request files into RequestSpec objects"""
    
    @staticmethod
    def parse_file(file_path: str) -> RequestSpec:
        """
        Parse a YAML request file
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            RequestSpec object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid or missing required fields
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Request file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise ValueError("Empty YAML file")
        
        return RequestParser.parse_dict(data)
    
    @staticmethod
    def parse_dict(data: Dict[str, Any]) -> RequestSpec:
        """
        Parse a dictionary into RequestSpec
        
        Args:
            data: Dictionary from YAML
            
        Returns:
            RequestSpec object
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        if 'Method' not in data:
            raise ValueError("Missing required field: Method")
        if 'Endpoint' not in data:
            raise ValueError("Missing required field: Endpoint")
        
        # Parse options
        options_data = data.get('Options', {})
        options = RequestOptions(
            insecure=options_data.get('insecure', False),
            timeout=options_data.get('timeout', 60)
        )
        
        # Parse body - only one type should be present
        json_body = None
        form_params = None
        text_body = None
        multipart_data = None
        
        if 'JsonBody' in data:
            json_body = data['JsonBody']
        elif 'FormParams' in data:
            form_params = data['FormParams']
        elif 'TextBody' in data:
            text_body = data['TextBody']
        elif 'MultipartData' in data:
            multipart_data = data['MultipartData']
        
        # Create RequestSpec
        spec = RequestSpec(
            method=data['Method'],
            endpoint=data['Endpoint'],
            define=data.get('Define', {}),
            path_params=data.get('PathParams', {}),
            query_params=data.get('QueryParams', {}),
            headers=data.get('Headers', {}),
            json_body=json_body,
            form_params=form_params,
            text_body=text_body,
            multipart_data=multipart_data,
            captures=data.get('Captures', {}),
            asserts=data.get('Asserts', {}),
            options=options
        )
        
        return spec
