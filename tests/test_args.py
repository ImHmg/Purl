"""Tests for argument parsing"""

import pytest

from purl.args import parse_arguments, PurlArgs


class TestPurlArgs:
    """Test PurlArgs class"""
    
    def test_init_with_single_file(self):
        """Test initialization with single file"""
        args = PurlArgs(['request.yaml'])
        assert args.request_files == ['request.yaml']
        assert args.env_names == []
        assert args.working_dir is None
    
    def test_init_with_multiple_files(self):
        """Test initialization with multiple files"""
        args = PurlArgs(['req1.yaml', 'req2.yaml'])
        assert args.request_files == ['req1.yaml', 'req2.yaml']
    
    def test_init_with_env_names(self):
        """Test initialization with environment names"""
        args = PurlArgs(['request.yaml'], env_names=['uat', 'prod'])
        assert args.env_names == ['uat', 'prod']
    
    def test_init_with_working_dir(self):
        """Test initialization with working directory"""
        args = PurlArgs(['request.yaml'], working_dir='/path/to/dir')
        assert args.working_dir == '/path/to/dir'


class TestParseArguments:
    """Test parse_arguments function"""
    
    def test_parse_single_file(self):
        """Test parsing single file"""
        args = parse_arguments(['request.yaml'])
        assert args.request_files == ['request.yaml']
        assert args.env_names == []
    
    def test_parse_multiple_files(self):
        """Test parsing multiple files"""
        args = parse_arguments(['req1.yaml', 'req2.yaml'])
        assert args.request_files == ['req1.yaml', 'req2.yaml']
    
    def test_parse_with_env(self):
        """Test parsing with environment config"""
        args = parse_arguments(['request.yaml', '-e', 'uat'])
        assert args.request_files == ['request.yaml']
        assert args.env_names == ['uat']
    
    def test_parse_with_multiple_envs(self):
        """Test parsing with multiple environment configs"""
        args = parse_arguments(['request.yaml', '-e', 'base', 'uat'])
        assert args.request_files == ['request.yaml']
        assert args.env_names == ['base', 'uat']
    
    def test_parse_with_working_dir(self):
        """Test parsing with working directory"""
        args = parse_arguments(['request.yaml', '-w', '/path/to/dir'])
        assert args.request_files == ['request.yaml']
        assert args.working_dir == '/path/to/dir'
    
    def test_parse_multiple_files_with_env(self):
        """Test parsing multiple files with environment"""
        args = parse_arguments(['req1.yaml', 'req2.yaml', '-e', 'uat'])
        assert args.request_files == ['req1.yaml', 'req2.yaml']
        assert args.env_names == ['uat']
    
    def test_parse_all_options(self):
        """Test parsing with all options"""
        args = parse_arguments([
            'req1.yaml', 'req2.yaml',
            '-e', 'base', 'uat',
            '-w', '/path/to/dir'
        ])
        assert args.request_files == ['req1.yaml', 'req2.yaml']
        assert args.env_names == ['base', 'uat']
        assert args.working_dir == '/path/to/dir'
    
    def test_parse_no_files_raises_error(self):
        """Test that parsing with no files raises error"""
        with pytest.raises(SystemExit):
            parse_arguments([])
