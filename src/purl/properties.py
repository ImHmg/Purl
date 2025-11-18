"""
Properties file I/O utilities
"""

from pathlib import Path
from typing import Dict


def read_properties(file_path: Path) -> Dict[str, str]:
    """Read properties file"""
    properties = {}
    
    if not file_path.exists():
        return properties
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                properties[key.strip()] = value.strip()
    
    return properties


def write_properties(file_path: Path, properties: Dict[str, str], header: str = None):
    """Write properties to file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        if header:
            f.write(f"# {header}\n")
        for key, value in properties.items():
            f.write(f"{key}={value}\n")
