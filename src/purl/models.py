"""
Data models for purl request specification
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List


@dataclass
class RequestOptions:
    """HTTP request options"""
    insecure: bool = False
    timeout: int = 60


@dataclass
class RequestSpec:
    """Complete HTTP request specification"""
    method: str
    endpoint: str
    
    # Optional sections
    define: Dict[str, str] = field(default_factory=dict)
    path_params: Dict[str, Any] = field(default_factory=dict)
    query_params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Body types (only one should be set)
    json_body: Optional[str] = None
    form_params: Optional[Dict[str, Any]] = None
    text_body: Optional[str] = None
    multipart_data: Optional[Dict[str, Any]] = None
    
    # Response handling
    captures: Dict[str, str] = field(default_factory=dict)
    asserts: Dict[str, str] = field(default_factory=dict)
    
    # Options
    options: RequestOptions = field(default_factory=RequestOptions)
    
    def get_body_type(self) -> Optional[str]:
        """
        Get the type of body being used
        
        Returns:
            'json', 'form', 'text', 'multipart', or None
        """
        if self.json_body is not None:
            return 'json'
        elif self.form_params is not None:
            return 'form'
        elif self.text_body is not None:
            return 'text'
        elif self.multipart_data is not None:
            return 'multipart'
        return None
    
    def get_body_content(self) -> Any:
        """
        Get the body content regardless of type
        
        Returns:
            The body content
        """
        body_type = self.get_body_type()
        if body_type == 'json':
            return self.json_body
        elif body_type == 'form':
            return self.form_params
        elif body_type == 'text':
            return self.text_body
        elif body_type == 'multipart':
            return self.multipart_data
        return None


@dataclass
class ParsedRequest:
    """Parsed and processed request ready for execution"""
    spec: RequestSpec
    resolved_endpoint: str
    resolved_headers: Dict[str, str]
    resolved_query_params: Dict[str, Any]
    resolved_body: Any
    context_variables: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for logging/display
        
        Returns:
            Dictionary representation
        """
        result = {
            'method': self.spec.method,
            'endpoint': self.resolved_endpoint,
            'headers': self.resolved_headers,
        }
        
        if self.resolved_query_params:
            result['query_params'] = self.resolved_query_params
        
        body_type = self.spec.get_body_type()
        if body_type:
            result['body_type'] = body_type
            result['body'] = self.resolved_body
        
        if self.spec.options.insecure:
            result['insecure'] = True
        
        if self.spec.options.timeout != 60:
            result['timeout'] = self.spec.options.timeout
        
        return result
