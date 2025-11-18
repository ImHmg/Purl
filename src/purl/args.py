"""
Argument parser for purl CLI
"""

import argparse
from typing import List, Optional

from . import __version__


class PurlArgs:
    """Singleton class for parsed command-line arguments"""
    
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
        self.request_files: List[str] = []
        self.config_names: List[str] = []
        self.working_dir: Optional[str] = None
        self.timeout: Optional[int] = None
        self.insecure: bool = False
        self.variables: dict = {}
        self.init: bool = False
        self.init_configs: List[str] = []
        self.generate: bool = False
        self.debug: bool = False
    
    def set_args(self, request_files: List[str], config_names: List[str] = None, working_dir: str = None,
                 timeout: int = None, insecure: bool = False, variables: dict = None,
                 init: bool = False, init_configs: List[str] = None, generate: bool = False, debug: bool = False):
        """Set parsed arguments"""
        self.request_files = request_files
        self.config_names = config_names or []
        self.working_dir = working_dir
        self.timeout = timeout
        self.insecure = insecure
        self.variables = variables or {}
        self.init = init
        self.init_configs = init_configs or []
        self.generate = generate
        self.debug = debug


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure argument parser
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog='purl',
        description='HTTP request testing tool with YAML configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\nExamples:
  purl request.yaml                              # Run single request
  purl request.yaml -c uat                       # Run with 'uat' config
  purl request.yaml -c uat --timeout 50          # Set request timeout to 50 seconds
  purl request.yaml -c uat --insecure            # Disable SSL verification
  purl request.yaml --var email=test@example.com # Override variable
  purl request.yaml --var user=john --var id=123 # Multiple variable overrides
  purl request.yaml -g                           # Generate fake data without executing
  purl request.yaml --debug                      # Run with debug mode enabled
  purl --init                                    # Initialize project structure
  purl --init -c dev uat prod                    # Initialize with multiple configs
  
For more information, visit: https://github.com/yourusername/purl
        """
    )
    
    parser.add_argument(
        'request_files',
        nargs='*',
        metavar='REQUEST_FILE',
        help='Path(s) to request YAML file(s). Multiple files will be executed sequentially.'
    )
    
    parser.add_argument(
        '-c', '--config',
        nargs='+',
        dest='config_names',
        metavar='CONFIG',
        help='Configuration name(s). Multiple configs can be specified, with later ones having higher priority.'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '-w', '--working-dir',
        dest='working_dir',
        metavar='DIR',
        help='Working directory (default: current directory)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        dest='timeout',
        metavar='SECONDS',
        help='Request timeout in seconds'
    )
    
    parser.add_argument(
        '--insecure',
        action='store_true',
        dest='insecure',
        help='Disable SSL certificate verification'
    )
    
    parser.add_argument(
        '--var',
        action='append',
        dest='variables',
        metavar='KEY=VALUE',
        help='Override variable (can be specified multiple times)'
    )
    
    parser.add_argument(
        '--init',
        action='store_true',
        dest='init',
        help='Initialize project directory structure with sample files'
    )
    
    parser.add_argument(
        '-g', '--generate',
        action='store_true',
        dest='generate',
        help='Generate fake data and print request without executing'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        dest='debug',
        help='Enable debug mode with verbose output'
    )
    
    return parser


def parse_arguments(args: List[str] = None) -> PurlArgs:
    """
    Parse command-line arguments and store in singleton
    
    Args:
        args: List of arguments to parse (default: sys.argv)
        
    Returns:
        PurlArgs singleton with parsed arguments
    """
    parser = create_argument_parser()
    parsed = parser.parse_args(args)
    
    # Parse variables from KEY=VALUE format
    variables = {}
    if parsed.variables:
        for var in parsed.variables:
            if '=' in var:
                key, value = var.split('=', 1)
                variables[key] = value
            else:
                raise ValueError(f"Invalid variable format: {var}. Expected KEY=VALUE")
    
    # Determine init_configs from config_names if --init is used
    init_configs = []
    if parsed.init and parsed.config_names:
        init_configs = parsed.config_names
    
    purl_args = PurlArgs()
    purl_args.set_args(
        request_files=parsed.request_files or [],
        config_names=parsed.config_names or [],
        working_dir=parsed.working_dir,
        timeout=parsed.timeout,
        insecure=parsed.insecure,
        variables=variables,
        init=parsed.init,
        init_configs=init_configs,
        generate=parsed.generate,
        debug=parsed.debug
    )
    
    return purl_args
