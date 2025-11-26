"""
Request processor - orchestrates parsing, variable resolution, and request preparation
"""

from typing import List, Dict, Any
import json

from .app_manager import AppManager
from .variables import VariableResolver, VariableContext
from .output import ColoredOutput, format_json_colored, format_dict_colored, print_http_request, print_http_response, print_captures, print_asserts
from .yaml_reader import read_yaml_file, parse_yaml_string
from .http_client import HttpClient
from .response_processor import ResponseProcessor
from .args import PurlArgs
from .script_executor import ScriptExecutor
from .curl_generator import CurlGenerator

class RequestProcessor:
    """Processes request files with variable substitution"""
    
    def __init__(self):
        """Initialize request processor"""
        self.app_manager = AppManager()
        self.resolver = VariableResolver()
        self.var_context = VariableContext()
        self.script_executor = ScriptExecutor()
        self.args = PurlArgs()
        self._initialized = False
    
    def initialize(self):
        """Initialize configuration and load variable sources from args"""
        # Initialize app (create folders/files)
        self.app_manager.initialize()
        
        # Reset and load all variables (including command-line overrides)
        self.var_context.reset()
        self.var_context.load()
        
        self._initialized = True
    
    def process_request(self, request_file: str) -> Dict[str, Any]:
        """
        Process a request file: read -> resolve -> read -> print
        
        Args:
            request_file: Path to the request YAML file
            
        Returns:
            Parsed YAML data as dictionary
        """
        if not self._initialized:
            raise RuntimeError("Processor not initialized. Call initialize() first.")
        
        # Step 1: Read file as string
        yaml_content = read_yaml_file(request_file)
        
        # Step 2: Resolve variables (pvars + configs, no context yet)
        resolved_pass1 = self.resolver.resolve_string(yaml_content)
        
        # Step 3: Read (parse) to get Define section
        yaml_data = parse_yaml_string(resolved_pass1)
        define_section = yaml_data.get('Define', {})
        
        # Step 4: Update context with Define variables
        if define_section:
            self.resolver.execute_define_section(define_section)
        
        # Step 4.5: Execute PreExec script (after Define section)
        pre_exec_script = yaml_data.get('PreExec')
        if pre_exec_script:
            self.script_executor.execute(pre_exec_script, yaml_data, "PreExec")
        
        # Step 5: Resolve variables again (context now has priority)
        resolved_pass2 = self.resolver.resolve_string(yaml_content)
        
        # Step 6: Read (parse) final YAML
        final_data = parse_yaml_string(resolved_pass2)
        
        # Step 7: Initialize http client
        http_client = HttpClient(final_data)

        if self.args.generate:
            curl_generator = CurlGenerator(http_client)
            curl_generator.print_curl()
            return
        
        # Step 8: Print HTTP request
        print_http_request(http_client)
        
        # Step 9: Execute HTTP request
        http_client.execute()
        
        # Step 10: Print HTTP response
        print_http_response(http_client)
        
        # Step 9: Process and print asserts
        response_processor = ResponseProcessor(http_client)
        asserts = response_processor.process_asserts()
        print_asserts(asserts)
        
        # Step 10: Process captures
        captures = response_processor.process_captures()
        
        # Step 11: Print captures
        print_captures(captures)
        
        # Step 12: Execute PostExec script (after everything done)
        post_exec_script = final_data.get('PostExec')
        if post_exec_script:
            self.script_executor.execute(post_exec_script, final_data, "PostExec")
        
        return {
            "status" : "complete",
            "file": request_file,
            "asserts": asserts,
            "captures": captures,
            "response": http_client.response,
            "request" : http_client.request,
            "request_spec": final_data
        }