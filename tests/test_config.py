"""Tests for configuration management"""

import pytest
import tempfile
import shutil
from pathlib import Path

from purl.config import ConfigManager


class TestConfigManager:
    """Test ConfigManager class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_initialize_creates_purl_directory(self, temp_dir):
        """Test that initialize creates .purl directory"""
        config = ConfigManager(temp_dir)
        config.initialize()
        
        assert config.purl_dir.exists()
        assert config.purl_dir.is_dir()
    
    def test_initialize_creates_pvars_file(self, temp_dir):
        """Test that initialize creates pvars.properties"""
        config = ConfigManager(temp_dir)
        config.initialize()
        
        assert config.pvars_path.exists()
        assert config.pvars_path.is_file()
    
    def test_initialize_creates_pcfg_file(self, temp_dir):
        """Test that initialize creates pcfg.properties"""
        config = ConfigManager(temp_dir)
        config.initialize()
        
        assert config.pcfg_path.exists()
        assert config.pcfg_path.is_file()
    
    def test_load_pvars_empty(self, temp_dir):
        """Test loading empty pvars file"""
        config = ConfigManager(temp_dir)
        config.initialize()
        
        pvars = config.load_pvars()
        assert pvars == {}
    
    def test_load_pvars_with_data(self, temp_dir):
        """Test loading pvars with data"""
        config = ConfigManager(temp_dir)
        config.initialize()
        
        # Write test data
        with open(config.pvars_path, 'w') as f:
            f.write("# Comment\n")
            f.write("key1=value1\n")
            f.write("key2=value2\n")
            f.write("\n")
            f.write("key3=value with spaces\n")
        
        pvars = config.load_pvars()
        assert pvars == {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value with spaces'
        }
    
    def test_save_pvars(self, temp_dir):
        """Test saving pvars"""
        config = ConfigManager(temp_dir)
        config.initialize()
        
        variables = {
            'api_key': 'test123',
            'base_url': 'https://example.com'
        }
        
        config.save_pvars(variables)
        loaded = config.load_pvars()
        
        assert loaded == variables
    
    def test_load_env_config(self, temp_dir):
        """Test loading environment config"""
        config = ConfigManager(temp_dir)
        config.initialize()
        
        # Create env directory and config file
        env_dir = Path(temp_dir) / 'env'
        env_dir.mkdir()
        
        env_file = env_dir / 'uat.properties'
        with open(env_file, 'w') as f:
            f.write("api_url=https://uat.example.com\n")
            f.write("api_key=uat_key_123\n")
        
        env_config = config.load_env_config('uat')
        assert env_config == {
            'api_url': 'https://uat.example.com',
            'api_key': 'uat_key_123'
        }
    
    def test_load_env_config_not_found(self, temp_dir):
        """Test loading non-existent environment config"""
        config = ConfigManager(temp_dir)
        config.initialize()
        
        with pytest.raises(FileNotFoundError):
            config.load_env_config('nonexistent')
