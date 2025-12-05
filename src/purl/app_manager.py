"""
Application manager for purl
Handles folder and file initialization
"""

from pathlib import Path
from typing import Optional
from .config import Config
from .args import PurlArgs
from .properties import read_properties


class AppManager:
    """Singleton class for purl application initialization"""
    
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
        self._setup_paths()
    
    def _setup_paths(self):
        """Setup paths from PurlArgs"""
        args = PurlArgs()
        self.working_dir = Path(args.working_dir) if args.working_dir else Path.cwd()
        self.purl_dir = self.working_dir / Config.PURL_DIR
        self.pvars_path = self.purl_dir / Config.PVARS_FILE
        self.pcfg_path = self.purl_dir / Config.PCFG_FILE
    
    def set_working_dir(self, working_dir: Optional[str] = None):
        """Set working directory"""
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.purl_dir = self.working_dir / Config.PURL_DIR
        self.pvars_path = self.purl_dir / Config.PVARS_FILE
        self.pcfg_path = self.purl_dir / Config.PCFG_FILE
    
    def initialize(self):
        """Initialize .purl directory and pvars.properties if they don't exist"""
        # Create .purl directory if it doesn't exist
        if not self.purl_dir.exists():
            self.purl_dir.mkdir(parents=True, exist_ok=True)
        
        # Create pvars.properties if it doesn't exist
        if not self.pvars_path.exists():
            self._create_pvars_file()
        
        # Create pcfg.properties if it doesn't exist
        # if not self.pcfg_path.exists():
        #     self._create_pcfg_file()
    
    def _create_pvars_file(self):
        """Create empty pvars.properties file"""
        with open(self.pvars_path, 'w', encoding='utf-8') as f:
            f.write("# purl variables file\n")
    
    def _create_pcfg_file(self):
        """Create default pcfg.properties file"""
        with open(self.pcfg_path, 'w', encoding='utf-8') as f:
            f.write("# purl configuration file\n")
            f.write(f"configs_dir={Config.DEFAULT_CONFIGS_DIR}\n")
    
    def get_pvars_path(self) -> Path:
        return self.pvars_path
    
    def get_configs_dir(self) -> str:
        """Get configs directory from pcfg.properties"""
        if not self.pcfg_path.exists():
            return Config.DEFAULT_CONFIGS_DIR
        
        pcfg = read_properties(self.pcfg_path)
        return pcfg.get('configs_dir', Config.DEFAULT_CONFIGS_DIR)
    
    def get_config_file_path(self, config_name: str) -> Path:
        """Get path to config file"""
        configs_dir = self.get_configs_dir()
        return self.working_dir / configs_dir / config_name
