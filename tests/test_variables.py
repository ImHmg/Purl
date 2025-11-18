"""Tests for variable resolution"""

import pytest

from purl.variables import VariableResolver, VariableManager


class TestVariableResolver:
    """Test VariableResolver class"""
    
    def test_resolve_simple_variable(self):
        """Test resolving a simple variable"""
        resolver = VariableResolver()
        sources = [{'name': 'John'}]
        
        result = resolver.resolve_string('Hello ${name}', sources)
        assert result == 'Hello John'
    
    def test_resolve_multiple_variables(self):
        """Test resolving multiple variables"""
        resolver = VariableResolver()
        sources = [{'first': 'John', 'last': 'Doe'}]
        
        result = resolver.resolve_string('${first} ${last}', sources)
        assert result == 'John Doe'
    
    def test_resolve_variable_priority(self):
        """Test variable resolution with priority"""
        resolver = VariableResolver()
        sources = [
            {'name': 'Priority1'},  # Highest priority
            {'name': 'Priority2'},
            {'name': 'Priority3'}
        ]
        
        result = resolver.resolve_string('${name}', sources)
        assert result == 'Priority1'
    
    def test_resolve_missing_variable(self):
        """Test resolving missing variable"""
        resolver = VariableResolver()
        sources = [{'name': 'John'}]
        
        result = resolver.resolve_string('${missing}', sources)
        assert result == '${missing}'
    
    def test_resolve_dict(self):
        """Test resolving variables in dictionary"""
        resolver = VariableResolver()
        sources = [{'base_url': 'https://example.com', 'version': 'v1'}]
        
        data = {
            'url': '${base_url}/api/${version}',
            'timeout': 30
        }
        
        result = resolver.resolve_dict(data, sources)
        assert result['url'] == 'https://example.com/api/v1'
        assert result['timeout'] == 30
    
    def test_resolve_nested_dict(self):
        """Test resolving variables in nested dictionary"""
        resolver = VariableResolver()
        sources = [{'token': 'abc123'}]
        
        data = {
            'headers': {
                'Authorization': 'Bearer ${token}'
            }
        }
        
        result = resolver.resolve_dict(data, sources)
        assert result['headers']['Authorization'] == 'Bearer abc123'
    
    def test_resolve_list(self):
        """Test resolving variables in list"""
        resolver = VariableResolver()
        sources = [{'env': 'production'}]
        
        data = ['${env}', 'test', '${env}-backup']
        
        result = resolver.resolve_list(data, sources)
        assert result == ['production', 'test', 'production-backup']
    
    def test_execute_define_section(self):
        """Test executing Define section"""
        resolver = VariableResolver()
        sources = [{'domain': 'example.com'}]
        
        define = {
            'email': 'user@${domain}',
            'api_url': 'https://api.${domain}'
        }
        
        context = resolver.execute_define_section(define, sources)
        assert context['email'] == 'user@example.com'
        assert context['api_url'] == 'https://api.example.com'
    
    def test_fake_random_string(self):
        """Test fake.random_string() function"""
        resolver = VariableResolver()
        sources = []
        
        result = resolver.resolve_string('${fake.random_string(5)}', sources)
        assert len(result) == 5
        assert result.isalnum() or '_' in result
    
    def test_fake_random_number(self):
        """Test fake.random_number() function"""
        resolver = VariableResolver()
        sources = []
        
        result = resolver.resolve_string('${fake.random_number(10)}', sources)
        assert len(result) == 10
        assert result.isdigit()
    
    def test_fake_email(self):
        """Test faker email generation"""
        resolver = VariableResolver()
        sources = []
        
        result = resolver.resolve_string('${fake.email()}', sources)
        assert '@' in result
    
    def test_nested_variable_resolution(self):
        """Test resolving variables that reference other variables"""
        resolver = VariableResolver()
        sources = [
            {'base': 'example.com'},
            {'full_url': 'https://${base}/api'}
        ]
        
        result = resolver.resolve_string('${full_url}', sources)
        assert result == 'https://example.com/api'


class TestVariableManager:
    """Test VariableManager class"""
    
    def test_build_variable_sources_priority(self):
        """Test building variable sources with correct priority"""
        manager = VariableManager()
        
        context = {'var': 'context_value'}
        env_configs = [
            {'var': 'env1_value'},
            {'var': 'env2_value'}
        ]
        pvars = {'var': 'pvars_value'}
        
        sources = manager.build_variable_sources(context, env_configs, pvars)
        
        # Priority: context > env2 > env1 > pvars
        assert sources[0] == context
        assert sources[1] == env_configs[1]  # env2 (last specified)
        assert sources[2] == env_configs[0]  # env1
        assert sources[3] == pvars
    
    def test_build_variable_sources_empty_env(self):
        """Test building variable sources with no environment configs"""
        manager = VariableManager()
        
        context = {'var': 'context_value'}
        env_configs = []
        pvars = {'var': 'pvars_value'}
        
        sources = manager.build_variable_sources(context, env_configs, pvars)
        
        assert len(sources) == 2
        assert sources[0] == context
        assert sources[1] == pvars
