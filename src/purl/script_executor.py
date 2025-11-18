"""
Script executor for PreExec and PostExec scripts
"""

from typing import Dict, Any, Optional
from .variables import VariableContext
from .faker_helper import PurlFaker
from .output import ColoredOutput


class ScriptExecutor:
    """Executes Python scripts with access to purl context (Singleton)"""
    
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
        self.var_context = VariableContext()  # Initialize internally (singleton)
        self.faker = PurlFaker().faker  # Direct access to faker instance
        
    def set_var(self, key: str, value: Any) -> None:
        """
        Store a variable in the pfvars
        
        Args:
            key: Variable name
            value: Variable value
        """
        self.var_context.put_variable(key, value)
        
    def get_var(self, key: str) -> Optional[Any]:
        """
        Get a variable
        
        Args:
            key: Variable name
            
        Returns:
            Variable value or None if not found
        """
        return self.var_context.get_variable(key)
    
    def execute(self, script: str, spec: Dict[str, Any], script_type: str = "script") -> None:
        """
        Execute a Python script with access to purl context
        
        Args:
            script: Python script as string
            spec: The parsed YAML spec as a dictionary
            script_type: Type of script (for error messages)
        """
        if not script or not script.strip():
            return
        
        try:
            # Create execution namespace with helper functions and objects
            exec_namespace = {
                'set_var': self.set_var,
                'get_var': self.get_var,
                'faker': self.faker,
                'spec': spec,
                # Add common imports that might be useful
                'json': __import__('json'),
                're': __import__('re'),
            }
            
            # Execute the script
            exec(script, exec_namespace)
            
        except Exception as e:
            ColoredOutput.error(f"Error executing {script_type}: {str(e)}")
            raise
