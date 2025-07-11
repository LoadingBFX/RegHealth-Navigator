"""
Test Configuration and Pre-flight Checks

This module provides configuration validation and pre-flight checks
before running the incremental update tests.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

# Add app directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class TestEnvironmentValidator:
    """Validates test environment and prerequisites."""
    
    def __init__(self):
        self.validation_results = {
            'overall_valid': False,
            'checks': {},
            'warnings': [],
            'errors': []
        }
    
    def validate_environment(self) -> Dict[str, Any]:
        """Run all validation checks."""
        logger.info("🔍 Validating test environment...")
        
        # Check imports
        self._check_imports()
        
        # Check file structure
        self._check_file_structure()
        
        # Check configuration
        self._check_configuration()
        
        # Check data availability
        self._check_data_availability()
        
        # Check API access
        self._check_api_access()
        
        # Determine overall validity
        critical_checks = ['imports', 'configuration', 'api_access']
        self.validation_results['overall_valid'] = all(
            self.validation_results['checks'].get(check, {}).get('passed', False)
            for check in critical_checks
        )
        
        return self.validation_results
    
    def _check_imports(self):
        """Check if all required modules can be imported."""
        imports_check = {
            'passed': True,
            'details': {},
            'errors': []
        }
        
        required_modules = [
            ('config_loader', 'ConfigLoader'),
            ('pipeline', 'ProcessingPipeline'),
            ('pipeline', 'AutoUpdatePipeline'),
            ('utils', 'DataPersistence'),
            ('faiss', None),
            ('numpy', None),
            ('xml.etree.ElementTree', None)
        ]
        
        for module_name, class_name in required_modules:
            try:
                if module_name == 'faiss':
                    import faiss
                    imports_check['details'][module_name] = '✅ Available'
                elif module_name == 'numpy':
                    import numpy as np
                    imports_check['details'][module_name] = '✅ Available'
                elif module_name == 'xml.etree.ElementTree':
                    import xml.etree.ElementTree as ET
                    imports_check['details'][module_name] = '✅ Available'
                elif module_name == 'config_loader':
                    from .config_loader import ConfigLoader
                    imports_check['details'][module_name] = '✅ Available'
                elif module_name == 'pipeline':
                    if class_name == 'ProcessingPipeline':
                        from .pipeline import ProcessingPipeline
                        imports_check['details']['ProcessingPipeline'] = '✅ Available'
                    elif class_name == 'AutoUpdatePipeline':
                        from .pipeline import AutoUpdatePipeline
                        imports_check['details']['AutoUpdatePipeline'] = '✅ Available'
                elif module_name == 'utils':
                    from .utils import DataPersistence
                    imports_check['details']['DataPersistence'] = '✅ Available'
            except ImportError as e:
                error_msg = f"❌ {module_name}: {e}"
                imports_check['details'][module_name] = error_msg
                imports_check['errors'].append(error_msg)
                imports_check['passed'] = False
        
        self.validation_results['checks']['imports'] = imports_check
    
    def _check_file_structure(self):
        """Check if required files and directories exist."""
        structure_check = {
            'passed': True,
            'details': {},
            'warnings': []
        }
        
        current_dir = Path(__file__).parent
        
        required_files = [
            'config_loader.py',
            'pipeline.py',
            'incremental_manager.py',
            'xml_chunker.py',
            'faiss_builder.py'
        ]
        
        for file_name in required_files:
            file_path = current_dir / file_name
            if file_path.exists():
                structure_check['details'][file_name] = '✅ Exists'
            else:
                warning_msg = f"⚠️ {file_name}: Not found"
                structure_check['details'][file_name] = warning_msg
                structure_check['warnings'].append(warning_msg)
        
        self.validation_results['checks']['file_structure'] = structure_check
    
    def _check_configuration(self):
        """Check configuration loading and validity."""
        config_check = {
            'passed': False,
            'details': {},
            'errors': []
        }
        
        try:
            from .config_loader import ConfigLoader
            
            config = ConfigLoader()
            processing_config = config.get_processing_config()
            validation = config.validate_config()
            
            config_check['details']['config_loading'] = '✅ Successful'
            config_check['details']['api_key_present'] = '✅ Present' if processing_config.get('api_key') else '❌ Missing'
            config_check['details']['data_dir'] = str(processing_config.get('data_dir', 'Not set'))
            config_check['details']['output_dir'] = str(processing_config.get('output_dir', 'Not set'))
            config_check['details']['model'] = processing_config.get('model', 'Not set')
            config_check['details']['chunk_words'] = processing_config.get('chunk_words', 'Not set')
            config_check['details']['days_back'] = processing_config.get('days_back', 'Not set')
            
            config_check['passed'] = validation.get('valid', False)
            
            if not validation.get('valid', False):
                for issue in validation.get('issues', []):
                    config_check['errors'].append(f"❌ {issue}")
        
        except Exception as e:
            config_check['errors'].append(f"❌ Configuration loading failed: {e}")
        
        self.validation_results['checks']['configuration'] = config_check
    
    def _check_data_availability(self):
        """Check if test data is available."""
        data_check = {
            'passed': True,
            'details': {},
            'warnings': []
        }
        
        try:
            from .config_loader import ConfigLoader
            config = ConfigLoader()
            processing_config = config.get_processing_config()
            
            data_dir = Path(processing_config['data_dir'])
            output_dir = Path(processing_config['output_dir'])
            
            # Check data directory
            if data_dir.exists():
                data_check['details']['data_directory'] = f"✅ {data_dir}"
                
                # Check for XML files in program directories
                program_dirs = ['MPFS', 'SNF', 'HOSPICE']
                for program_dir in program_dirs:
                    program_path = data_dir / program_dir
                    if program_path.exists():
                        xml_files = list(program_path.glob('*.xml'))
                        count = len(xml_files)
                        data_check['details'][f'{program_dir}_xml_files'] = f"✅ {count} files"
                        if count == 0:
                            data_check['warnings'].append(f"⚠️ No XML files in {program_dir}")
                    else:
                        data_check['details'][f'{program_dir}_directory'] = f"❌ Not found"
                        data_check['warnings'].append(f"⚠️ {program_dir} directory not found")
            else:
                data_check['details']['data_directory'] = f"❌ {data_dir} not found"
                data_check['warnings'].append(f"⚠️ Data directory not found: {data_dir}")
            
            # Check output directory
            if output_dir.exists():
                data_check['details']['output_directory'] = f"✅ {output_dir}"
                
                # Check for existing processing files
                processing_files = ['chunks.json', 'faiss.index', 'faiss_metadata.json']
                for file_name in processing_files:
                    file_path = output_dir / file_name
                    if file_path.exists():
                        size = file_path.stat().st_size
                        data_check['details'][file_name] = f"✅ {size:,} bytes"
                    else:
                        data_check['details'][file_name] = "❌ Not found"
            else:
                data_check['details']['output_directory'] = f"❌ {output_dir} not found"
        
        except Exception as e:
            data_check['warnings'].append(f"⚠️ Data availability check failed: {e}")
        
        self.validation_results['checks']['data_availability'] = data_check
    
    def _check_api_access(self):
        """Check API access without making actual calls."""
        api_check = {
            'passed': False,
            'details': {},
            'errors': []
        }
        
        try:
            # Check if API key is available
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                api_check['details']['api_key_env'] = f"✅ Present ({len(api_key)} chars)"
                api_check['passed'] = True
                
                # Basic validation of API key format
                if api_key.startswith('sk-') and len(api_key) > 20:
                    api_check['details']['api_key_format'] = "✅ Valid format"
                else:
                    api_check['details']['api_key_format'] = "⚠️ Unusual format"
            else:
                api_check['details']['api_key_env'] = "❌ Not found"
                api_check['errors'].append("❌ OPENAI_API_KEY environment variable not set")
            
            # Check if .env file exists
            env_file = Path(__file__).parent.parent.parent.parent / '.env'
            if env_file.exists():
                api_check['details']['env_file'] = f"✅ Found at {env_file}"
            else:
                api_check['details']['env_file'] = "⚠️ .env file not found"
        
        except Exception as e:
            api_check['errors'].append(f"❌ API access check failed: {e}")
        
        self.validation_results['checks']['api_access'] = api_check
    
    def print_validation_report(self):
        """Print detailed validation report."""
        print("\n" + "="*60)
        print("🔍 TEST ENVIRONMENT VALIDATION REPORT")
        print("="*60)
        
        overall_status = "✅ READY" if self.validation_results['overall_valid'] else "❌ NOT READY"
        print(f"Overall Status: {overall_status}")
        print("")
        
        # Print each check
        for check_name, check_result in self.validation_results['checks'].items():
            status = "✅ PASSED" if check_result.get('passed', False) else "❌ FAILED"
            print(f"{status} - {check_name.replace('_', ' ').title()}")
            
            # Print details
            for detail_name, detail_value in check_result.get('details', {}).items():
                print(f"    {detail_name}: {detail_value}")
            
            # Print errors
            for error in check_result.get('errors', []):
                print(f"    {error}")
            
            # Print warnings
            for warning in check_result.get('warnings', []):
                print(f"    {warning}")
            
            print("")
        
        # Print overall warnings and errors
        if self.validation_results['warnings']:
            print("⚠️ WARNINGS:")
            for warning in self.validation_results['warnings']:
                print(f"  {warning}")
            print("")
        
        if self.validation_results['errors']:
            print("❌ ERRORS:")
            for error in self.validation_results['errors']:
                print(f"  {error}")
            print("")
        
        print("="*60)


def main():
    """Run validation and print report."""
    validator = TestEnvironmentValidator()
    results = validator.validate_environment()
    validator.print_validation_report()
    
    if results['overall_valid']:
        print("🎉 Environment is ready for testing!")
        return 0
    else:
        print("💥 Environment validation failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())