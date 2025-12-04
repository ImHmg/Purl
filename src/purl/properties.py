"""YAML-based configuration I/O utilities"""

from pathlib import Path
from typing import Any, Dict

import yaml


def _ensure_mapping(data: Any, file_path: Path) -> Dict[str, Any]:
    """Validate YAML content is a mapping."""
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {file_path}, got {type(data).__name__}")
    return data


def read_properties(file_path: Path) -> Dict[str, Any]:
    """Read YAML configuration file into a dictionary"""
    if not file_path.exists():
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    return _ensure_mapping(data, file_path)


def write_properties(file_path: Path, properties: Dict[str, Any], header: str = None):
    """Write dictionary values to a YAML configuration file"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        if header:
            f.write(f"# {header}\n")
        yaml.safe_dump(properties or {}, f, sort_keys=False, default_flow_style=False)
