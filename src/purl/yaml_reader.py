"""
YAML file reader
"""

import yaml
from typing import Dict, Any


def read_yaml_file(file_path: str) -> str:
    """
    Read YAML file as string
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        File content as string
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_yaml_string(yaml_content: str) -> Dict[str, Any]:
    """
    Parse YAML string to dictionary
    
    Args:
        yaml_content: YAML content as string
        
    Returns:
        Parsed YAML as dictionary
    """
    return yaml.safe_load(yaml_content)


def read_and_parse_yaml(file_path: str) -> Dict[str, Any]:
    """
    Read and parse YAML file
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Parsed YAML as dictionary
    """
    content = read_yaml_file(file_path)
    return parse_yaml_string(content)
