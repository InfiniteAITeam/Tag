"""
Tagging Code Validator

This module validates that generated tagging code is correct and follows patterns.
"""

import re
from typing import Dict, List, Any, Tuple


class TaggingValidator:
    """Validates tagging code implementations."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
    
    def validate(self, file_content: str, file_path: str, event_type: str) -> Dict[str, Any]:
        """
        Validate tagging implementation in file.
        
        Args:
            file_content: Full file content
            file_path: Path to file (for context)
            event_type: 'page_load', 'click', or 'error'
            
        Returns:
            Validation report
        """
        self.errors = []
        self.warnings = []
        self.suggestions = []
        
        # Run all validations
        self._check_imports(file_content, file_path)
        self._check_hook_usage(file_content)
        
        if event_type == 'page_load':
            self._check_page_load_pattern(file_content)
        elif event_type == 'click':
            self._check_click_pattern(file_content)
        elif event_type == 'error':
            self._check_error_pattern(file_content)
        
        self._check_syntax(file_content)
        self._check_code_quality(file_content)
        
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
        }
    
    def _check_imports(self, content: str, file_path: str):
        """Validate import statements."""
        # Check if useTagging is imported
        if 'useTagging' not in content:
            self.errors.append("Missing: import { useTagging } from '../Tagging'")
            return
        
        # Check import path format
        import_patterns = [
            r"import\s*{\s*useTagging\s*}\s*from\s*['\"]\.+/Tagging['\"]",
            r"import\s*{\s*useTagging\s*}\s*from\s*['\"]\.+/Tagging/index['\"]",
        ]
        
        found_import = False
        for pattern in import_patterns:
            if re.search(pattern, content):
                found_import = True
                break
        
        if not found_import:
            # Look for any useTagging import to give specific error
            if re.search(r"import.*useTagging.*from.*['\"].*Tagging", content):
                # Import exists but with /index.js which is wrong
                if '/index.js' in content:
                    self.warnings.append(
                        "Import path includes '/index.js' - should be '../Tagging' not '../Tagging/index.js'"
                    )
            else:
                self.errors.append("useTagging import not found or incorrect format")
    
    def _check_hook_usage(self, content: str):
        """Validate hook is properly called and destructured."""
        # Check if useTagging() is called
        if 'useTagging()' not in content:
            self.errors.append("Missing: useTagging() call in component")
            return
        
        # Check destructuring pattern
        destructure_pattern = r"const\s*{\s*([^}]+)\s*}\s*=\s*useTagging\(\)"
        matches = re.findall(destructure_pattern, content)
        
        if not matches:
            self.errors.append("useTagging() not properly destructured")
            return
        
        # Get destructured functions
        destructured = matches[0].split(',')
        destructured = [fn.strip() for fn in destructured]
        
        # Check for unnecessary destructuring
        all_functions = {'trackPageLoad', 'trackPageChange', 'trackPageNotification'}
        destructured_set = set(destructured)
        
        unused = all_functions - destructured_set
        for fn in destructured_set:
            if fn not in all_functions:
                self.warnings.append(f"Unknown function destructured: {fn}")
            elif fn not in content:
                self.suggestions.append(
                    f"Function {fn} is destructured but never used - remove from destructuring"
                )
    
    def _check_page_load_pattern(self, content: str):
        """Validate page load tracking pattern."""
        # Check for useEffect
        if 'useEffect' not in content:
            self.errors.append("Missing: useEffect hook for page load tracking")
            return
        
        # Check for empty dependency array
        if not re.search(r"useEffect\s*\(\s*\(\s*\)\s*=>\s*{[^}]*}, \[\]", content, re.DOTALL):
            self.warnings.append(
                "useEffect for tracking should have empty dependency array []"
            )
        
        # Check for trackPageLoad call
        if 'trackPageLoad' not in content:
            self.errors.append("Missing: trackPageLoad() call")
            return
        
        # Check trackPageLoad parameters
        page_load_pattern = r"trackPageLoad\s*\(\s*{\s*pageName\s*:\s*['\"][^'\"]*['\"],\s*flow\s*:\s*['\"][^'\"]*['\"]\s*}\s*\)"
        if not re.search(page_load_pattern, content):
            self.warnings.append(
                "trackPageLoad should have pageName and flow parameters: "
                "trackPageLoad({ pageName: 'PageName', flow: 'flow-name' })"
            )
    
    def _check_click_pattern(self, content: str):
        """Validate click/interaction tracking pattern."""
        # Check for trackPageChange call
        if 'trackPageChange' not in content:
            self.errors.append("Missing: trackPageChange() call for interaction tracking")
            return
        
        # Check trackPageChange is in event handler (look for patterns like handleX, onClick, etc.)
        handler_pattern = r"(const\s+handle\w+|onClick|onChange|onSubmit|on\w+)\s*=\s*\(.*?\)\s*=>\s*{"
        if re.search(handler_pattern, content):
            # Check if trackPageChange appears near the start of handler
            handlers = re.finditer(handler_pattern, content)
            for handler in handlers:
                handler_start = handler.start()
                next_500 = content[handler_start:handler_start + 500]
                if 'trackPageChange' in next_500:
                    # Verify it's the first substantive call
                    handler_body_start = next_500.find('{') + 1
                    handler_body = next_500[handler_body_start:]
                    first_call_match = re.search(r"(trackPageChange|\w+\()", handler_body)
                    if first_call_match and 'trackPageChange' not in first_call_match.group(1):
                        self.warnings.append(
                            "trackPageChange should be the FIRST call in event handler"
                        )
    
    def _check_error_pattern(self, content: str):
        """Validate error/notification tracking pattern."""
        # Check for trackPageNotification call
        if 'trackPageNotification' not in content:
            self.errors.append("Missing: trackPageNotification() call for error tracking")
            return
        
        # Check for try-catch or error handler
        if 'try' not in content or 'catch' not in content:
            self.warnings.append(
                "Error tracking should be in try-catch block or error handler"
            )
        
        # Check trackPageNotification parameters
        notification_pattern = r"trackPageNotification\s*\(\s*['\"]?\w+['\"]?\s*,\s*.*?\s*,\s*['\"]?\w+['\"]?\s*\)"
        if not re.search(notification_pattern, content, re.DOTALL):
            self.warnings.append(
                "trackPageNotification should have three parameters: "
                "(eventName, message, id)"
            )
    
    def _check_syntax(self, content: str):
        """Check for basic JavaScript syntax errors."""
        # Count brackets
        if content.count('{') != content.count('}'):
            self.errors.append("Mismatched braces - { } count mismatch")
        
        if content.count('(') != content.count(')'):
            self.errors.append("Mismatched parentheses - ( ) count mismatch")
        
        if content.count('[') != content.count(']'):
            self.errors.append("Mismatched brackets - [ ] count mismatch")
        
        # Check quotes
        single_quotes = content.count("'")
        double_quotes = content.count('"')
        backticks = content.count('`')
        
        if single_quotes % 2 != 0:
            self.errors.append("Unmatched single quotes")
        
        if double_quotes % 2 != 0:
            self.errors.append("Unmatched double quotes")
        
        if backticks % 2 != 0:
            self.errors.append("Unmatched backticks")
    
    def _check_code_quality(self, content: str):
        """Check code quality and best practices."""
        # Check for duplicate imports
        import_count = len(re.findall(r"import\s*{\s*useTagging\s*}", content))
        if import_count > 1:
            self.warnings.append(f"useTagging imported {import_count} times - should be once")
        
        # Check for console.log (debugging code)
        if 'console.log' in content:
            self.suggestions.append("Remove console.log statements before production")
        
        # Check for meaningful tracking parameters
        if re.search(r"pageName\s*:\s*['\"]page['\"]", content, re.IGNORECASE):
            self.suggestions.append(
                "Use more descriptive page name instead of generic 'page'"
            )
        
        if re.search(r"flow\s*:\s*['\"]flow['\"]", content, re.IGNORECASE):
            self.suggestions.append(
                "Use more descriptive flow name instead of generic 'flow'"
            )
        
        # Check for hardcoded error messages
        if 'error.message' in content and 'trackPageNotification' in content:
            if not re.search(r"trackPageNotification\(['\"]?\w+['\"]?\s*,\s*error\.message", content):
                self.suggestions.append(
                    "Consider using error.message in trackPageNotification for better error tracking"
                )


def validate_tagging_code(file_content: str, file_path: str, event_type: str) -> Dict[str, Any]:
    """
    Validate tagging implementation.
    
    Args:
        file_content: Full file content
        file_path: Path to file
        event_type: Type of event ('page_load', 'click', 'error')
        
    Returns:
        Validation report with errors, warnings, and suggestions
    """
    validator = TaggingValidator()
    return validator.validate(file_content, file_path, event_type)


def is_valid_tagging_code(validation_result: Dict[str, Any]) -> bool:
    """Check if tagging code is valid (no errors)."""
    return validation_result.get('valid', False)


def get_validation_report(validation_result: Dict[str, Any]) -> str:
    """Generate human-readable validation report."""
    report = "## Tagging Code Validation Report\n\n"
    
    if validation_result['valid']:
        report += "✓ **VALID** - No errors found\n\n"
    else:
        report += "✗ **INVALID** - Errors found\n\n"
    
    if validation_result['errors']:
        report += "### Errors\n"
        for i, error in enumerate(validation_result['errors'], 1):
            report += f"{i}. {error}\n"
        report += "\n"
    
    if validation_result['warnings']:
        report += "### Warnings\n"
        for i, warning in enumerate(validation_result['warnings'], 1):
            report += f"{i}. {warning}\n"
        report += "\n"
    
    if validation_result['suggestions']:
        report += "### Suggestions\n"
        for i, suggestion in enumerate(validation_result['suggestions'], 1):
            report += f"{i}. {suggestion}\n"
    
    return report
