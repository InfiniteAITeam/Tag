"""
Data-Track Attribute Analyzer and Generator

This module identifies interactive elements (buttons, divs with onClick, etc.)
and generates appropriate data-track attribute values using LLM intelligence.

No hardcoding - full LLM-driven analysis.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ElementType(Enum):
    """Types of interactive elements"""
    BUTTON = "button"
    DIV = "div"
    SPAN = "span"
    INPUT = "input"
    LINK = "link"
    ANCHOR = "anchor"
    CUSTOM = "custom"


@dataclass
class InteractiveElement:
    """Represents an interactive element in JSX/JavaScript"""
    element_type: ElementType
    line_number: int
    column_start: int
    element_html: str
    inner_text: str
    has_data_track: bool
    attributes: Dict[str, str]
    parent_component: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "element_type": self.element_type.value,
            "line_number": self.line_number,
            "column_start": self.column_start,
            "element_html": self.element_html[:100] + "..." if len(self.element_html) > 100 else self.element_html,
            "inner_text": self.inner_text,
            "has_data_track": self.has_data_track,
            "attributes": self.attributes,
            "parent_component": self.parent_component
        }


class ElementExtractor:
    """
    Identifies interactive elements in React/JSX files
    
    Finds:
    - <button> elements
    - Elements with onClick handlers
    - <Link> components
    - <a> anchor tags
    
    Uses regex patterns - all values passed to LLM for final validation
    """
    
    def __init__(self, file_path: str, file_content: str):
        """
        Initialize extractor with file content
        
        Args:
            file_path: Path to the file
            file_content: Full content of the file
        """
        self.file_path = Path(file_path)
        self.file_content = file_content
        self.lines = file_content.split('\n')
        self.elements: List[InteractiveElement] = []
    
    def extract_all_interactive_elements(self) -> List[InteractiveElement]:
        """
        Extract all interactive elements from the file
        
        Returns:
            List of InteractiveElement objects
        """
        self.elements = []
        
        # Find all button elements
        self._find_button_elements()
        
        # Find all onClick handlers (div, span, input, etc.)
        self._find_onclick_elements()
        
        # Find Link and anchor components
        self._find_routing_components()
        
        # Sort by line number
        self.elements.sort(key=lambda x: (x.line_number, x.column_start))
        
        return self.elements
    
    def _find_button_elements(self):
        """Find all <button> elements"""
        # Pattern: <button ... >...</button>
        # Matches: <button>, <button className="...">, <button onClick={...}>, etc.
        pattern = r'<button\s+([^>]*)>([^<]*)</button>'
        
        for line_num, line in enumerate(self.lines, 1):
            for match in re.finditer(pattern, line, re.IGNORECASE | re.DOTALL):
                attributes_str = match.group(1)
                inner_text = match.group(2).strip()
                
                # Parse attributes
                attributes = self._parse_attributes(attributes_str)
                has_data_track = 'data-track' in attributes
                
                element = InteractiveElement(
                    element_type=ElementType.BUTTON,
                    line_number=line_num,
                    column_start=match.start(),
                    element_html=match.group(0),
                    inner_text=inner_text,
                    has_data_track=has_data_track,
                    attributes=attributes
                )
                
                self.elements.append(element)
    
    def _find_onclick_elements(self):
        """Find all elements with onClick handlers"""
        # Pattern: elements with onClick={...} or onClick="..."
        # Matches: <div onClick=...>, <span onClick=...>, <input onClick=...>
        element_types = ['div', 'span', 'input', 'label', 'a']
        
        for elem_type in element_types:
            # Self-closing: <element onClick=... />
            self_closing_pattern = f'<{elem_type}\\s+([^>]*onClick[^>]*)\\s*/>'
            
            # Opening tag: <element onClick=...>
            opening_pattern = f'<{elem_type}\\s+([^>]*onClick[^>]*)>'
            
            for line_num, line in enumerate(self.lines, 1):
                # Self-closing elements
                for match in re.finditer(self_closing_pattern, line, re.IGNORECASE):
                    attributes_str = match.group(1)
                    attributes = self._parse_attributes(attributes_str)
                    has_data_track = 'data-track' in attributes
                    
                    element = InteractiveElement(
                        element_type=ElementType(elem_type),
                        line_number=line_num,
                        column_start=match.start(),
                        element_html=match.group(0),
                        inner_text="",
                        has_data_track=has_data_track,
                        attributes=attributes
                    )
                    
                    self.elements.append(element)
                
                # Opening tag (extract text from this and following lines)
                for match in re.finditer(opening_pattern, line, re.IGNORECASE):
                    attributes_str = match.group(1)
                    attributes = self._parse_attributes(attributes_str)
                    has_data_track = 'data-track' in attributes
                    
                    # Extract text until closing tag
                    closing_tag = f'</{elem_type}>'
                    closing_pos = line.find(closing_tag, match.end())
                    
                    inner_text = ""
                    full_html = match.group(0)
                    
                    if closing_pos != -1:
                        # Closing tag on same line
                        inner_text = line[match.end():closing_pos].strip()
                        full_html = line[match.start():closing_pos + len(closing_tag)]
                    else:
                        # Closing tag on next line
                        inner_text = line[match.end():].strip()
                        
                        # Look for closing tag in next lines
                        for next_line_idx in range(line_num, min(line_num + 10, len(self.lines))):
                            next_line = self.lines[next_line_idx]
                            closing_pos = next_line.find(closing_tag)
                            
                            if closing_pos != -1:
                                if next_line_idx == line_num:
                                    inner_text = next_line[:closing_pos].strip()
                                break
                    
                    element = InteractiveElement(
                        element_type=ElementType(elem_type),
                        line_number=line_num,
                        column_start=match.start(),
                        element_html=full_html[:100],  # Truncate for storage
                        inner_text=inner_text,
                        has_data_track=has_data_track,
                        attributes=attributes
                    )
                    
                    self.elements.append(element)
    
    def _find_routing_components(self):
        """Find Link and routing components"""
        # Pattern: <Link ... >...</Link>
        pattern = r'<Link\s+([^>]*)>([^<]*)</Link>'
        
        for line_num, line in enumerate(self.lines, 1):
            for match in re.finditer(pattern, line):
                attributes_str = match.group(1)
                inner_text = match.group(2).strip()
                
                attributes = self._parse_attributes(attributes_str)
                has_data_track = 'data-track' in attributes
                
                element = InteractiveElement(
                    element_type=ElementType.LINK,
                    line_number=line_num,
                    column_start=match.start(),
                    element_html=match.group(0),
                    inner_text=inner_text,
                    has_data_track=has_data_track,
                    attributes=attributes
                )
                
                self.elements.append(element)
    
    def _parse_attributes(self, attributes_str: str) -> Dict[str, str]:
        """
        Parse HTML attributes from string
        
        Handles:
        - className="value"
        - onClick={handler}
        - data-track="value"
        - onClick="value"
        """
        attributes = {}
        
        # Pattern: attr="value" or attr={value} or attr='value'
        pattern = r'(\w+[-\w]*)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|\{([^}]*)\})'
        
        for match in re.finditer(pattern, attributes_str):
            attr_name = match.group(1)
            attr_value = match.group(2) or match.group(3) or match.group(4)
            attributes[attr_name] = attr_value
        
        return attributes
    
    def get_elements_summary(self) -> Dict[str, int]:
        """Get count of elements by type"""
        summary = {}
        for elem in self.elements:
            key = f"{elem.element_type.value}_with_data_track" if elem.has_data_track else elem.element_type.value
            summary[key] = summary.get(key, 0) + 1
        return summary


class ValueSanitizer:
    """
    Sanitizes and validates data-track values
    
    Ensures:
    - Valid kebab-case format
    - No special characters
    - Reasonable length
    - Meaningful content
    """
    
    @staticmethod
    def sanitize(raw_value: str, max_length: int = 50) -> str:
        """
        Convert raw text to valid data-track value
        
        Args:
            raw_value: Raw text extracted from element
            max_length: Maximum length of value
        
        Returns:
            Sanitized kebab-case value
        """
        if not raw_value or not isinstance(raw_value, str):
            return ""
        
        # 1. Strip whitespace
        value = raw_value.strip()
        
        # 2. Remove HTML tags
        value = re.sub(r'<[^>]+>', '', value)
        
        # 3. Convert to lowercase
        value = value.lower()
        
        # 4. Replace spaces and underscores with hyphens
        value = re.sub(r'[\s_]+', '-', value)
        
        # 5. Remove any character that's not alphanumeric or hyphen
        value = re.sub(r'[^a-z0-9\-]', '', value)
        
        # 6. Remove consecutive hyphens
        value = re.sub(r'-+', '-', value)
        
        # 7. Remove leading/trailing hyphens
        value = value.strip('-')
        
        # 8. Limit length
        value = value[:max_length]
        
        return value
    
    @staticmethod
    def is_valid_value(value: str) -> bool:
        """
        Check if value is valid for data-track attribute
        
        Valid if:
        - Non-empty
        - Only alphanumeric and hyphens
        - Between 2 and 50 characters
        """
        if not value or not isinstance(value, str):
            return False
        
        if not re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', value) and not re.match(r'^[a-z0-9]$', value):
            return False
        
        return 2 <= len(value) <= 50
    
    @staticmethod
    def extract_text_from_element(element: InteractiveElement) -> str:
        """
        Extract meaningful text from element
        
        Tries:
        1. Inner text (direct text content)
        2. title attribute
        3. aria-label attribute
        4. placeholder attribute
        5. alt attribute
        """
        # 1. Use inner text if available
        if element.inner_text:
            return element.inner_text
        
        # 2. Try title attribute
        if 'title' in element.attributes:
            return element.attributes['title']
        
        # 3. Try aria-label
        if 'aria-label' in element.attributes:
            return element.attributes['aria-label']
        
        # 4. Try placeholder
        if 'placeholder' in element.attributes:
            return element.attributes['placeholder']
        
        # 5. Try alt
        if 'alt' in element.attributes:
            return element.attributes['alt']
        
        # Fallback: use element type
        return element.element_type.value
