"""
Variable substitution and management
"""

import re
from typing import Dict, Any, List, Optional
from .faker_helper import PurlFaker
from .output import ColoredOutput
from .properties import read_properties, write_properties
from .app_manager import AppManager
from .args import PurlArgs
from .yaml_reader import parse_yaml_string


class VariableContext:
    """Singleton class to hold all variable sources with priority"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.pvars: Dict[str, Any] = {}
        self.configs: List[Dict[str, Any]] = []
        self.tempvars: Dict[str, Any] = {}
        self.purl_faker = PurlFaker()
    
    def reset(self):
        """Reset all variables"""
        self.pvars = {}
        self.configs = []
        self.tempvars = {}
    
    def load_pvars(self):
        """Load pvars from file"""
        app_manager = AppManager()
        pvars_path = app_manager.get_pvars_path()
        self.pvars = read_properties(pvars_path)
    
    def save_pvars(self):
        """Save pvars to file"""
        app_manager = AppManager()
        pvars_path = app_manager.get_pvars_path()
        write_properties(pvars_path, self.pvars, "purl variables file")
    
    def load_configs(self, config_names: List[str]):
        """Load configs from files"""
        import sys
        app_manager = AppManager()
        configs = []
        
        if config_names:
            for config_name in config_names:
                config_file_path = app_manager.get_config_file_path(config_name + ".yaml")
                if not config_file_path.exists():
                    ColoredOutput.error(f"Config not found: {config_file_path}")
                    ColoredOutput.info(f"Available configs should be in: {app_manager.get_configs_dir()}/")
                    sys.exit(1)
                config = read_properties(config_file_path)
                configs.append(config)
        
        self.configs = configs
    
    def load_configs_from_str(self, config_content: str):
        """Load configs from YAML string"""
        parsed_config = parse_yaml_string(config_content)
        self.configs = [parsed_config] if parsed_config else []

    def load(self):
        """Load all variables (pvars, configs, and command-line overrides) from args"""
        args = PurlArgs()
        self.load_pvars()
        self.load_configs(args.config_names)
        
        # Apply command-line variable overrides to tempvars (highest priority)
        if args.variables:
            for key, value in args.variables.items():
                self.put_tempvars(key, value)
    
    def put_tempvars(self, key: str, value: Any):
        """Set a variable"""
        self.tempvars[key] = value
    
    def put_variable(self, key: str, value: Any):
        """Set a variable"""
        self.pvars[key] = value
        self.save_pvars()
    
    def get_variable(self, var_name: str) -> Optional[Any]:
        """
        Get variable value with priority: tempvars > configs > pvars
        
        Args:
            var_name: Variable name
            
        Returns:
            Variable value or None if not found
        """
        # Priority 1: tempvars
        if var_name in self.tempvars:
            return self.tempvars[var_name]
        
        # Priority 2: Configs (last specified has highest priority)
        for config in reversed(self.configs):
            if var_name in config:
                return config[var_name]
        
        # Priority 3: pvars
        if var_name in self.pvars:
            return self.pvars[var_name]
        
        return None


class VariableResolver:
    """Handles variable substitution using singleton context - strings only"""
    
    # Pattern to match ${variable_name}
    VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    def __init__(self):
        """Initialize variable resolver"""
        self.var_context = VariableContext()
    
    def resolve_string(self, value: str) -> str:
        """
        Resolve variables in a string using singleton context
        
        Args:
            value: String potentially containing ${variable} references
            
        Returns:
            String with variables resolved
        """
        if not isinstance(value, str):
            return str(value)
        
        def replace_var(match):
            var_name = match.group(1)
            
            # Check if it's a fake data function call
            if var_name.startswith('fake.'):
                return self.var_context.purl_faker.generate(var_name)
            
            # Look up variable in context (handles priority internally)
            var_value = self.var_context.get_variable(var_name)
            
            if var_value is not None:
                # If the value itself contains variables, resolve them recursively
                if isinstance(var_value, str) and '${' in var_value:
                    return self.resolve_string(var_value)
                return str(var_value)
            
            # Variable not found, return as-is
            return match.group(0)
        
        return self.VAR_PATTERN.sub(replace_var, value)
    
    def execute_define_section(self, define: Dict[str, str]) -> Dict[str, str]:
        """
        Execute Define section to create context variables
        All values are strings after resolution
        
        Args:
            define: Define section dictionary
            
        Returns:
            Dictionary of defined variables (all strings)
        """
        var_context = VariableContext()  
        for key, value in define.items():
            # Resolve the value (may contain variables or fake functions)
            # All values are treated as strings
            resolved_value = self.resolve_string(str(value))
            var_context.put_variable(key, resolved_value)

