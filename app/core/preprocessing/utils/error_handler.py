"""
Error Handling Utilities

Provides standardized error handling patterns and result formatting
for consistent error management across the preprocessing package.

Example:
    @handle_operation("file processing", success_fields={'files_processed': 0})
    def process_files(file_paths):
        # Your processing logic here
        return {'files_processed': len(file_paths), 'chunks_created': 100}
        
    result = process_files(['file1.xml', 'file2.xml'])
    # Result: {
    #     'status': 'success',
    #     'files_processed': 2,
    #     'chunks_created': 100,
    #     'message': '✅ file processing completed successfully'
    # }
"""

import logging
import functools
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Custom exception for preprocessing operations."""
    
    def __init__(self, message: str, operation: str = None, details: Dict = None):
        """
        Initialize ProcessingError.
        
        Args:
            message: Error description
            operation: Name of the operation that failed
            details: Additional error context
        """
        super().__init__(message)
        self.operation = operation
        self.details = details or {}


@dataclass
class OperationResult:
    """Standardized result format for all operations."""
    status: str  # 'success', 'error', 'partial_success'
    message: str
    data: Dict[str, Any] = None
    error: str = None
    operation: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        result = {
            'status': self.status,
            'message': self.message
        }
        
        if self.data:
            result.update(self.data)
        if self.error:
            result['error'] = self.error
        if self.operation:
            result['operation'] = self.operation
            
        return result


def handle_operation(
    operation_name: str,
    success_fields: Optional[Dict[str, Any]] = None,
    error_fields: Optional[Dict[str, Any]] = None,
    logger_name: Optional[str] = None
) -> Callable:
    """
    Decorator for standardized operation error handling and result formatting.
    
    Args:
        operation_name: Human-readable name of the operation
        success_fields: Default fields to include in successful results
        error_fields: Default fields to include in error results  
        logger_name: Custom logger name (uses operation_name if None)
        
    Returns:
        Decorated function that returns standardized OperationResult
        
    Example:
        @handle_operation("XML parsing", success_fields={'chunks': 0})
        def parse_xml(file_path):
            chunks = parse_file(file_path)
            return {'chunks': len(chunks), 'file_path': file_path}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            operation_logger = logging.getLogger(logger_name or operation_name.replace(' ', '_'))
            
            try:
                # Execute the original function
                result = func(*args, **kwargs)
                
                # Ensure result is a dictionary
                if not isinstance(result, dict):
                    result = {}
                
                # Add default success fields
                if success_fields:
                    for key, default_value in success_fields.items():
                        if key not in result:
                            result[key] = default_value
                
                # Create success result
                operation_result = OperationResult(
                    status='success',
                    message=f'✅ {operation_name} completed successfully',
                    data=result,
                    operation=operation_name
                )
                
                operation_logger.info(operation_result.message)
                return operation_result.to_dict()
                
            except ProcessingError as e:
                # Handle custom processing errors
                error_data = error_fields.copy() if error_fields else {}
                error_data.update(e.details)
                
                operation_result = OperationResult(
                    status='error',
                    message=f'❌ {operation_name} failed: {str(e)}',
                    data=error_data,
                    error=str(e),
                    operation=operation_name
                )
                
                operation_logger.error(operation_result.message)
                return operation_result.to_dict()
                
            except Exception as e:
                # Handle unexpected errors
                error_data = error_fields.copy() if error_fields else {}
                
                operation_result = OperationResult(
                    status='error',
                    message=f'❌ {operation_name} failed with unexpected error',
                    data=error_data,
                    error=str(e),
                    operation=operation_name
                )
                
                operation_logger.error(f"{operation_result.message}: {e}")
                return operation_result.to_dict()
                
        return wrapper
    return decorator


def ensure_success(result: Dict[str, Any], operation: str = "operation") -> Dict[str, Any]:
    """
    Validate that an operation result indicates success, raise ProcessingError if not.
    
    Args:
        result: Operation result dictionary
        operation: Operation name for error context
        
    Returns:
        The result dictionary if successful
        
    Raises:
        ProcessingError: If the operation was not successful
        
    Example:
        result = some_operation()
        ensure_success(result, "file processing")
        # Continues if result['status'] == 'success', raises ProcessingError otherwise
    """
    if not isinstance(result, dict):
        raise ProcessingError(f"Invalid result format: expected dict, got {type(result)}", operation)
    
    status = result.get('status')
    if status != 'success':
        error_msg = result.get('error', 'Unknown error')
        raise ProcessingError(f"{operation} failed: {error_msg}", operation, result)
        
    return result


def combine_results(results: list, operation: str = "batch operation") -> Dict[str, Any]:
    """
    Combine multiple operation results into a single result.
    
    Args:
        results: List of operation result dictionaries
        operation: Name of the batch operation
        
    Returns:
        Combined result with aggregated status and data
        
    Example:
        results = [process_file(f) for f in files]
        combined = combine_results(results, "batch file processing")
        # Returns summary of all operations
    """
    if not results:
        return {
            'status': 'success',
            'message': f'✅ {operation} completed (no items to process)',
            'total_operations': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
    
    successful = [r for r in results if r.get('status') == 'success']
    failed = [r for r in results if r.get('status') == 'error']
    partial = [r for r in results if r.get('status') == 'partial_success']
    
    # Determine overall status
    if not failed and not partial:
        overall_status = 'success'
        message = f'✅ {operation} completed successfully'
    elif failed:
        overall_status = 'partial_success' if successful else 'error'
        message = f'⚠️ {operation} completed with {len(failed)} failures'
    else:
        overall_status = 'partial_success'
        message = f'⚠️ {operation} completed with partial success'
    
    # Collect errors
    errors = []
    for result in failed + partial:
        if 'error' in result:
            errors.append(result['error'])
    
    return {
        'status': overall_status,
        'message': message,
        'total_operations': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'partial_success': len(partial),
        'errors': errors,
        'operation': operation
    }