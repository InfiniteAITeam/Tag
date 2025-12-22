"""
Smart Data-Track Attribute Applier

Uses Vegas LLM to intelligently:
1. Identify interactive elements
2. Extract semantic values
3. Generate and apply data-track attributes
4. Preserve all other code
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from tools.data_track_extractor import (
    ElementExtractor, InteractiveElement, ElementType, ValueSanitizer
)
from tools.vegas_llm_utils import VegasLLMWrapper


class DataTrackPromptBuilder:
    """Builds intelligent prompts for LLM-driven data-track attribute generation"""
    
    @staticmethod
    def build_element_detection_prompt(file_content: str, file_path: str) -> str:
        """
        Build prompt to have LLM identify interactive elements
        
        Args:
            file_content: Full file content
            file_path: Path to file
        
        Returns:
            Prompt for LLM
        """
        prompt = f"""You are a React/JSX code analyzer specialized in identifying interactive elements.

## FILE ANALYSIS TASK

**File**: {file_path}

**File Content**:
```javascript
{file_content}
```

## YOUR TASK

Identify ALL interactive elements in this React component:

1. **All <button> elements** - ANY button tag
2. **All elements with onClick handlers** - div, span, input, label, etc. with onClick={{...}}
3. **All <Link> components** - React Router Link elements
4. **All <a> tags** - Anchor/hyperlink elements

## FOR EACH ELEMENT FOUND

Provide:
- **line_number**: Which line the element starts on (1-indexed)
- **element_type**: button | div | span | input | link | a | other
- **inner_text**: Text content or label of the element
- **has_onClick**: true if element has onClick handler
- **has_data_track**: true if already has data-track attribute
- **attributes**: Important attributes (className, title, aria-label, etc.)
- **html_snippet**: A short snippet of the HTML (first 80 chars)

## OUTPUT FORMAT

Return ONLY valid JSON (no markdown, no explanation):
```json
{{
  "elements_found": N,
  "elements": [
    {{
      "line_number": 42,
      "element_type": "button",
      "inner_text": "Pay Bill",
      "has_onClick": true,
      "has_data_track": false,
      "attributes": {{"className": "btn-primary", "type": "submit"}},
      "html_snippet": "<button className=\"btn-primary\" onClick={{...}}>Pay Bill</button>"
    }},
    {{
      "line_number": 65,
      "element_type": "div",
      "inner_text": "Close Modal",
      "has_onClick": true,
      "has_data_track": false,
      "attributes": {{"className": "modal-close"}},
      "html_snippet": "<div className=\"modal-close\" onClick={{handleClose}}>Close Modal</div>"
    }}
  ]
}}
```

## IMPORTANT RULES

- Include EVERY interactive element, even if small
- If element already has data-track, still include it (mark has_data_track: true)
- Extract exact text as shown in UI
- Be thorough - check entire file carefully
- Return valid JSON only
"""
        return prompt
    
    @staticmethod
    def build_value_generation_prompt(
        file_content: str,
        file_path: str,
        element: Dict[str, Any],
        extracted_text: str
    ) -> str:
        """
        Build prompt to have LLM generate appropriate data-track value
        
        Args:
            file_content: Full file content
            file_path: Path to file
            element: Element info dict
            extracted_text: Text extracted from element
        
        Returns:
            Prompt for LLM
        """
        element_type = element.get("element_type", "element")
        line_number = element.get("line_number", "?")
        html_snippet = element.get("html_snippet", "")
        
        prompt = f"""You are an analytics expert specializing in semantic labeling.

## CONTEXT

**File**: {file_path}
**Line**: {line_number}
**Element Type**: {element_type}
**Element HTML**: {html_snippet}

## FILE CONTEXT (for understanding purpose):
```javascript
{file_content}
```

## TASK

Generate an appropriate `data-track` attribute value for this element.

The value should:
1. Be **semantic** - clearly indicate what the element does
2. Be **concise** - brief but meaningful
3. Use **kebab-case** - lowercase with hyphens, NO spaces or underscores
4. Be **actionable** - describe the action/button purpose
5. Have **max 50 characters**
6. Use only **alphanumeric and hyphens**

## EXTRACTED INFORMATION

From the element, we extracted:
- **Inner Text/Label**: "{extracted_text}"
- **Element Type**: {element_type}

## EXAMPLES

```
Button with text "Pay Bill" → data-track="pay-bill"
Button with text "Submit Payment" → data-track="submit-payment"
Div with text "Close Modal" → data-track="close-modal"
Button with aria-label "Edit Profile" → data-track="edit-profile"
Input with placeholder "Enter Name" → data-track="enter-name"
Link to "/dashboard" → data-track="go-to-dashboard"
Button with icon only → data-track="[element-type]-button" or derive from context
```

## OUTPUT

Return ONLY valid JSON (no markdown, no explanation):
```json
{{
  "data_track_value": "the-value-here",
  "reasoning": "Brief explanation of why this value",
  "confidence": "high|medium|low"
}}
```

For example:
```json
{{
  "data_track_value": "pay-bill",
  "reasoning": "Button allows user to pay their bill. Inner text is 'Pay Bill'",
  "confidence": "high"
}}
```

## CRITICAL RULES

- Value must be kebab-case (no spaces, underscores, or special chars)
- Max 50 characters
- Must be meaningful - describe the action
- If text is very generic ("Click Here", "Submit"), use element context
- Return valid JSON only
"""
        return prompt
    
    @staticmethod
    def build_code_generation_prompt(
        file_content: str,
        file_path: str,
        elements_to_modify: List[Dict[str, Any]]
    ) -> str:
        """
        Build prompt to have LLM apply data-track attributes to code
        
        Args:
            file_content: Original file content
            file_path: Path to file
            elements_to_modify: List of elements with their data-track values
        
        Returns:
            Prompt for LLM
        """
        modifications_json = json.dumps(elements_to_modify, indent=2)
        
        prompt = f"""You are a code transformation expert specializing in React/JSX.

## FILE TO MODIFY

**Path**: {file_path}

**Original Content**:
```javascript
{file_content}
```

## MODIFICATIONS NEEDED

Apply data-track attributes to the following elements:

```json
{modifications_json}
```

Each item in the list specifies:
- **line_number**: Where in the file (1-indexed)
- **element_type**: What kind of element (button, div, span, etc.)
- **data_track_value**: The data-track value to add
- **current_html**: Current HTML snippet

## YOUR TASK

1. Add `data-track="{value}"` attribute to each element
2. Place data-track right after the opening tag, before other attributes
3. Preserve ALL other code exactly as-is
4. Don't modify anything except adding the data-track attribute
5. Keep proper formatting and indentation
6. Handle JSX properly (use quotes for attribute values)

## RULES

- Add data-track to ONLY the specified elements
- Do NOT add if data-track already exists
- Preserve className, onClick, all other attributes
- Keep JSX syntax correct
- Don't break any code
- Return the COMPLETE updated file

## TRANSFORMATION EXAMPLE

**Before**:
```jsx
<button onClick={handleSubmit} className="btn-primary">
  Pay Bill
</button>
```

**After**:
```jsx
<button data-track="pay-bill" onClick={handleSubmit} className="btn-primary">
  Pay Bill
</button>
```

**Another example**:
```jsx
<div onClick={closeModal} className="modal-overlay">Close</div>
```
becomes:
```jsx
<div data-track="close-modal" onClick={closeModal} className="modal-overlay">Close</div>
```

## OUTPUT

Return ONLY the complete updated file content as valid JavaScript/JSX code.
No JSON, no markdown code blocks, just the updated file content.

Start directly with the code (e.g., `import ...` or `function ...`).
"""
        return prompt
    
    @staticmethod
    def build_check_already_exists_prompt(
        file_content: str,
        element: Dict[str, Any]
    ) -> str:
        """
        Build prompt to check if element already has data-track
        
        Args:
            file_content: File content
            element: Element to check
        
        Returns:
            Prompt for LLM
        """
        prompt = f"""You are a code analyzer.

## TASK

Does this element already have a data-track attribute?

**Element Type**: {element.get("element_type")}
**Line**: {element.get("line_number")}
**HTML Snippet**: {element.get("html_snippet")}

## FILE CONTEXT
```javascript
{file_content}
```

Return ONLY JSON:
```json
{{
  "has_data_track": true/false,
  "reason": "explanation"
}}
```

Example:
```json
{{
  "has_data_track": true,
  "reason": "Element already has data-track=\"pay-bill\" attribute"
}}
```
"""
        return prompt


class DataTrackApplier:
    """
    Applies data-track attributes to interactive elements using LLM
    """
    
    def __init__(self, llm_client: VegasLLMWrapper):
        """Initialize with LLM client"""
        self.client = llm_client
        self.prompt_builder = DataTrackPromptBuilder()
    
    def extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response
        
        Args:
            response: LLM response text
        
        Returns:
            Parsed JSON dict, or empty dict if parsing fails
        """
        if not response:
            return {}
        
        try:
            # Try direct JSON parse first
            return json.loads(response)
        except Exception:
            pass
        
        # Try to find JSON in response
        start = response.find('{')
        if start == -1:
            return {}
        
        # Find matching closing brace
        depth = 0
        for i in range(start, len(response)):
            if response[i] == '{':
                depth += 1
            elif response[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(response[start:i+1])
                    except:
                        pass
        
        return {}
    
    def detect_elements_with_llm(
        self,
        file_content: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to detect all interactive elements
        
        Args:
            file_content: File content
            file_path: Path to file
        
        Returns:
            List of detected elements
        """
        prompt = self.prompt_builder.build_element_detection_prompt(
            file_content,
            file_path
        )
        
        try:
            response = self.client.invoke(prompt)
            result = self.extract_json_from_response(response)
            
            elements = result.get("elements", [])
            return elements
            
        except Exception as e:
            print(f"  ⚠️  LLM element detection failed: {e}")
            return []
    
    def generate_value_with_llm(
        self,
        file_content: str,
        file_path: str,
        element: Dict[str, Any],
        extracted_text: str
    ) -> Tuple[str, str, str]:
        """
        Use LLM to generate appropriate data-track value
        
        Args:
            file_content: File content
            file_path: Path to file
            element: Element info
            extracted_text: Extracted text from element
        
        Returns:
            (data_track_value, reasoning, confidence)
        """
        prompt = self.prompt_builder.build_value_generation_prompt(
            file_content,
            file_path,
            element,
            extracted_text
        )
        
        try:
            response = self.client.invoke(prompt)
            result = self.extract_json_from_response(response)
            
            value = result.get("data_track_value", "")
            reasoning = result.get("reasoning", "")
            confidence = result.get("confidence", "low")
            
            # Validate and sanitize value
            sanitizer = ValueSanitizer()
            value = sanitizer.sanitize(value)
            
            if not sanitizer.is_valid_value(value):
                # Fallback to sanitized extracted text
                value = sanitizer.sanitize(extracted_text)
            
            return (value, reasoning, confidence)
            
        except Exception as e:
            print(f"  ⚠️  LLM value generation failed: {e}")
            # Fallback: sanitize extracted text
            sanitizer = ValueSanitizer()
            value = sanitizer.sanitize(extracted_text)
            return (value, f"Fallback due to LLM error: {e}", "low")
    
    def apply_data_track_with_llm(
        self,
        file_content: str,
        file_path: str,
        elements_to_modify: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Use LLM to apply data-track attributes to code
        
        Args:
            file_content: Original file content
            file_path: Path to file
            elements_to_modify: List of elements with data-track values
        
        Returns:
            (updated_file_content, modification_log)
        """
        if not elements_to_modify:
            return (file_content, [])
        
        prompt = self.prompt_builder.build_code_generation_prompt(
            file_content,
            file_path,
            elements_to_modify
        )
        
        try:
            response = self.client.invoke(prompt)
            
            # LLM returns updated file content directly (not JSON)
            updated_content = response.strip()
            
            # Log modifications
            log = []
            for elem in elements_to_modify:
                log.append({
                    "line": elem.get("line_number"),
                    "element_type": elem.get("element_type"),
                    "data_track_value": elem.get("data_track_value"),
                    "status": "applied"
                })
            
            return (updated_content, log)
            
        except Exception as e:
            print(f"  ⚠️  LLM code generation failed: {e}")
            return (file_content, [{"status": "error", "reason": str(e)}])
