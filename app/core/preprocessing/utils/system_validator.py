"""
System Validation Utilities

Provides comprehensive validation and health checking capabilities
for the preprocessing system components and data consistency.

Example:
    validator = SystemValidator()
    
    # Add component validators
    validator.add_validator('chunks', lambda: validate_chunks_file())
    validator.add_validator('faiss', lambda: validate_faiss_index())
    
    # Run validation
    report = validator.validate_all()
    if report['valid']:
        print("System is healthy")
    else:
        print(f"Issues found: {report['issues']}")
"""

import os
from pathlib import Path
from typing import Dict, List, Callable, Any, Optional, Tuple
import logging
from datetime import datetime

from .error_handler import handle_operation, ProcessingError
from .data_persistence import DataPersistence

logger = logging.getLogger(__name__)


class ValidationResult:
    """Represents the result of a validation check."""
    
    def __init__(
        self,
        component: str,
        valid: bool,
        message: str = "",
        issues: List[str] = None,
        warnings: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize validation result.
        
        Args:
            component: Name of the component being validated
            valid: Whether the component passed validation
            message: Summary message
            issues: List of critical issues (cause validation failure)
            warnings: List of non-critical warnings
            metadata: Additional validation data
        """
        self.component = component
        self.valid = valid
        self.message = message
        self.issues = issues or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            'component': self.component,
            'valid': self.valid,
            'message': self.message,
            'issues': self.issues,
            'warnings': self.warnings,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class SystemValidator:
    """
    Comprehensive system validation and health checking.
    
    Manages validation of individual components and provides
    system-wide health reports with detailed diagnostics.
    """
    
    def __init__(self):
        """Initialize SystemValidator."""
        self.validators: Dict[str, Callable[[], ValidationResult]] = {}
        self.required_components: set = set()
        self.optional_components: set = set()
        
        logger.debug("SystemValidator initialized")
    
    def add_validator(
        self,
        component_name: str,
        validator_func: Callable[[], ValidationResult],
        required: bool = True
    ) -> None:
        """
        Add a component validator.
        
        Args:
            component_name: Name of the component
            validator_func: Function that returns ValidationResult
            required: Whether this component is required for system health
            
        Example:
            def validate_chunks():
                # Validation logic here
                return ValidationResult('chunks', True, "Chunks file is valid")
            
            validator.add_validator('chunks', validate_chunks, required=True)
        """
        self.validators[component_name] = validator_func
        
        if required:
            self.required_components.add(component_name)
        else:
            self.optional_components.add(component_name)
        
        logger.debug(f"Added {'required' if required else 'optional'} validator: {component_name}")
    
    def remove_validator(self, component_name: str) -> bool:
        """
        Remove a component validator.
        
        Args:
            component_name: Name of the component to remove
            
        Returns:
            True if validator was removed, False if not found
        """
        if component_name in self.validators:
            del self.validators[component_name]
            self.required_components.discard(component_name)
            self.optional_components.discard(component_name)
            logger.debug(f"Removed validator: {component_name}")
            return True
        return False
    
    @handle_operation("component validation")
    def validate_component(self, component_name: str) -> Dict[str, Any]:
        """
        Validate a specific component.
        
        Args:
            component_name: Name of the component to validate
            
        Returns:
            Validation result dictionary
            
        Example:
            result = validator.validate_component('chunks')
            if result['status'] == 'success' and result['valid']:
                print("Chunks component is healthy")
        """
        if component_name not in self.validators:
            raise ProcessingError(f"No validator found for component: {component_name}")
        
        try:
            validation_result = self.validators[component_name]()
            
            if not isinstance(validation_result, ValidationResult):
                raise ProcessingError(f"Validator for {component_name} returned invalid result type")
            
            result_dict = validation_result.to_dict()
            result_dict['component_type'] = 'required' if component_name in self.required_components else 'optional'
            
            return result_dict
            
        except Exception as e:
            logger.error(f"Validation failed for {component_name}: {e}")
            error_result = ValidationResult(
                component_name,
                False,
                f"Validation error: {str(e)}",
                issues=[f"Validator execution failed: {str(e)}"]
            )
            return error_result.to_dict()
    
    @handle_operation("system validation")
    def validate_all(self, stop_on_error: bool = False) -> Dict[str, Any]:
        """
        Validate all registered components.
        
        Args:
            stop_on_error: Whether to stop validation on first error
            
        Returns:
            Comprehensive validation report
            
        Example:
            report = validator.validate_all()
            print(f"System valid: {report['valid']}")
            for issue in report['issues']:
                print(f"Issue: {issue}")
        """
        results = {}
        all_issues = []
        all_warnings = []
        required_valid = True
        optional_issues = []
        
        # Validate all components
        for component_name in self.validators:
            try:
                component_result = self.validate_component(component_name)
                results[component_name] = component_result
                
                # Collect issues and warnings
                component_issues = component_result.get('issues', [])
                component_warnings = component_result.get('warnings', [])
                
                all_issues.extend([f"{component_name}: {issue}" for issue in component_issues])
                all_warnings.extend([f"{component_name}: {warning}" for warning in component_warnings])
                
                # Check if required component failed
                if component_name in self.required_components and not component_result.get('valid', False):
                    required_valid = False
                
                # Track optional component issues
                if component_name in self.optional_components and not component_result.get('valid', False):
                    optional_issues.append(component_name)
                
                # Stop on error if requested
                if stop_on_error and component_issues:
                    break
                    
            except Exception as e:
                logger.error(f"Critical error validating {component_name}: {e}")
                all_issues.append(f"{component_name}: Critical validation error - {str(e)}")
                
                if component_name in self.required_components:
                    required_valid = False
                
                if stop_on_error:
                    break
        
        # Determine overall system health
        system_valid = required_valid and len(all_issues) == 0
        
        # Generate summary message
        if system_valid:
            message = "✅ All system components are healthy"
        elif required_valid:
            message = f"⚠️ System functional with {len(all_warnings)} warnings"
        else:
            message = f"❌ System has {len(all_issues)} critical issues"
        
        # Create comprehensive report
        report = {
            'valid': system_valid,
            'message': message,
            'issues': all_issues,
            'warnings': all_warnings,
            'component_results': results,
            'summary': {
                'total_components': len(self.validators),
                'required_components': len(self.required_components),
                'optional_components': len(self.optional_components),
                'required_valid': required_valid,
                'total_issues': len(all_issues),
                'total_warnings': len(all_warnings),
                'optional_issues': len(optional_issues)
            }
        }
        
        logger.info(f"System validation completed: {message}")
        
        return report
    
    @staticmethod
    def validate_file_exists(
        file_path: str,
        component_name: str,
        required: bool = True
    ) -> ValidationResult:
        """
        Standard file existence validator.
        
        Args:
            file_path: Path to file to check
            component_name: Name of the component for reporting
            required: Whether file is required
            
        Returns:
            ValidationResult for the file check
            
        Example:
            result = SystemValidator.validate_file_exists(
                'chunks.json', 'chunks', required=True
            )
        """
        file_path = Path(file_path)
        
        if file_path.exists():
            file_stats = DataPersistence.get_file_stats(file_path)
            return ValidationResult(
                component_name,
                True,
                f"File exists: {file_path}",
                metadata={
                    'file_path': str(file_path),
                    'size_bytes': file_stats.get('size_bytes', 0),
                    'exists': True
                }
            )
        else:
            if required:
                return ValidationResult(
                    component_name,
                    False,
                    f"Required file missing: {file_path}",
                    issues=[f"File does not exist: {file_path}"],
                    metadata={'file_path': str(file_path), 'exists': False}
                )
            else:
                return ValidationResult(
                    component_name,
                    True,
                    f"Optional file missing: {file_path}",
                    warnings=[f"Optional file not found: {file_path}"],
                    metadata={'file_path': str(file_path), 'exists': False}
                )
    
    @staticmethod
    def validate_directory_exists(
        dir_path: str,
        component_name: str,
        required: bool = True,
        check_writable: bool = False
    ) -> ValidationResult:
        """
        Standard directory existence and permissions validator.
        
        Args:
            dir_path: Path to directory to check
            component_name: Name of the component for reporting
            required: Whether directory is required
            check_writable: Whether to check write permissions
            
        Returns:
            ValidationResult for the directory check
        """
        dir_path = Path(dir_path)
        issues = []
        warnings = []
        metadata = {'directory_path': str(dir_path)}
        
        if not dir_path.exists():
            if required:
                issues.append(f"Required directory does not exist: {dir_path}")
            else:
                warnings.append(f"Optional directory does not exist: {dir_path}")
            metadata['exists'] = False
        else:
            metadata['exists'] = True
            
            if not dir_path.is_dir():
                issues.append(f"Path exists but is not a directory: {dir_path}")
                metadata['is_directory'] = False
            else:
                metadata['is_directory'] = True
                
                if check_writable:
                    try:
                        # Test write access
                        test_file = dir_path / '.write_test'
                        test_file.touch()
                        test_file.unlink()
                        metadata['writable'] = True
                    except Exception:
                        issues.append(f"Directory is not writable: {dir_path}")
                        metadata['writable'] = False
        
        valid = len(issues) == 0
        message = f"Directory check: {dir_path} {'✅ OK' if valid else '❌ Issues'}"
        
        return ValidationResult(component_name, valid, message, issues, warnings, metadata)
    
    @staticmethod
    def validate_json_file(
        file_path: str,
        component_name: str,
        required_keys: Optional[List[str]] = None,
        max_size_mb: Optional[float] = None
    ) -> ValidationResult:
        """
        Validate JSON file format and content.
        
        Args:
            file_path: Path to JSON file
            component_name: Component name for reporting
            required_keys: List of required top-level keys
            max_size_mb: Maximum file size in MB
            
        Returns:
            ValidationResult for the JSON file
        """
        file_path = Path(file_path)
        issues = []
        warnings = []
        metadata = {'file_path': str(file_path)}
        
        # Check file existence
        if not file_path.exists():
            issues.append(f"JSON file does not exist: {file_path}")
            return ValidationResult(component_name, False, "File missing", issues, warnings, metadata)
        
        # Check file size
        file_stats = DataPersistence.get_file_stats(file_path)
        size_mb = file_stats.get('size_bytes', 0) / (1024 * 1024)
        metadata['size_mb'] = round(size_mb, 2)
        
        if max_size_mb and size_mb > max_size_mb:
            warnings.append(f"JSON file is large: {size_mb:.1f}MB > {max_size_mb}MB")
        
        # Validate JSON format
        load_result = DataPersistence.load_json(file_path)
        if load_result['status'] != 'success':
            issues.append(f"Invalid JSON format: {load_result.get('error')}")
            return ValidationResult(component_name, False, "Invalid JSON", issues, warnings, metadata)
        
        data = load_result['data']
        metadata['json_valid'] = True
        
        # Check required keys
        if required_keys and isinstance(data, dict):
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                issues.append(f"Missing required keys: {missing_keys}")
        
        # Add content statistics
        if isinstance(data, list):
            metadata['item_count'] = len(data)
        elif isinstance(data, dict):
            metadata['key_count'] = len(data)
        
        valid = len(issues) == 0
        message = f"JSON validation: {file_path} {'✅ Valid' if valid else '❌ Invalid'}"
        
        return ValidationResult(component_name, valid, message, issues, warnings, metadata)
    
    def create_standard_validators(
        self,
        chunks_file: str,
        faiss_index: str,
        faiss_metadata: str,
        tracking_file: str,
        data_directory: str
    ) -> None:
        """
        Create standard validators for common preprocessing components.
        
        Args:
            chunks_file: Path to chunks.json file
            faiss_index: Path to FAISS index file
            faiss_metadata: Path to FAISS metadata file
            tracking_file: Path to file tracking data
            data_directory: Path to source data directory
            
        Example:
            validator.create_standard_validators(
                'output/chunks.json',
                'output/faiss.index', 
                'output/faiss_metadata.json',
                'output/tracking.json',
                'data/xml'
            )
        """
        # Chunks file validator
        self.add_validator(
            'chunks_file',
            lambda: self.validate_json_file(
                chunks_file, 'chunks_file', max_size_mb=500
            ),
            required=True
        )
        
        # FAISS index validator
        self.add_validator(
            'faiss_index',
            lambda: self.validate_file_exists(faiss_index, 'faiss_index', required=True),
            required=True
        )
        
        # FAISS metadata validator  
        self.add_validator(
            'faiss_metadata',
            lambda: self.validate_json_file(
                faiss_metadata, 'faiss_metadata', max_size_mb=100
            ),
            required=True
        )
        
        # Tracking file validator
        self.add_validator(
            'tracking_file',
            lambda: self.validate_json_file(tracking_file, 'tracking_file'),
            required=False
        )
        
        # Data directory validator
        self.add_validator(
            'data_directory',
            lambda: self.validate_directory_exists(
                data_directory, 'data_directory', required=True, check_writable=False
            ),
            required=True
        )
        
        logger.info("Standard validators created for all components")