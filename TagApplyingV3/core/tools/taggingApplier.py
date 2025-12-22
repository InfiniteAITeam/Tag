"""
Tagging Applier Module

This module applies tagging to React components based on the JSON specification.
It reads the actionable_item.json and applies appropriate tags to the
source files listed in the specification.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class TaggingApplier:
    """Applies corporate tagging standards to React components based on JSON specification."""
    
    def __init__(self, json_spec_path: str, repo_path: str):
        """
        Initialize the tagging applier.
        
        Args:
            json_spec_path: Path to the JSON specification file (e.g., actionable_item.json)
            repo_path: Path to the cloned repository
        """
        self.json_spec_path = Path(json_spec_path)
        self.repo_path = Path(repo_path)
        self.spec = self._load_spec()
        self.tagging_utils_path = self.repo_path / "src" / "pages" / "ExpressStore" / "Tagging"
        
    def _load_spec(self) -> Dict[str, Any]:
        """Load and parse the JSON specification."""
        if not self.json_spec_path.exists():
            raise FileNotFoundError(f"JSON spec not found: {self.json_spec_path}")
        
        with open(self.json_spec_path, 'r') as f:
            spec = json.load(f)
        logger.info(f"Loaded spec from {self.json_spec_path}")
        return spec
    
    def get_files_to_tag(self) -> List[Dict[str, Any]]:
        """
        Extract all files that need tagging from the spec.
        
        Handles three formats:
        1. Array format (NEW): [{"file": "path", "description": "...", ...}, {...}]
        2. Items format: {"items": [{"file": "path", "description": "...", ...}, {...}]}
        3. Hierarchical format: {"file_path:lines": {metadata}, ...}
        
        Returns:
            List of dictionaries containing file info:
            {
                'sourceFile': 'src/pages/ExpressStore/Landing/index.js',
                'description': {...full metadata object...}
            }
        """
        files_to_tag = []
        
        # Handle array format (preferred)
        if isinstance(self.spec, list):
            for item in self.spec:
                if isinstance(item, dict) and "file" in item:
                    file_entry = {
                        'sourceFile': item['file'],
                        'description': item,
                    }
                    files_to_tag.append(file_entry)
        
        # Handle items format
        elif isinstance(self.spec, dict) and "items" in self.spec:
            items = self.spec.get("items") or []
            for item in items:
                if isinstance(item, dict) and "file" in item:
                    file_entry = {
                        'sourceFile': item['file'],
                        'description': item,
                    }
                    files_to_tag.append(file_entry)
        
        # Handle hierarchical format (legacy)
        elif isinstance(self.spec, dict):
            for file_path, metadata in self.spec.items():
                # Remove line number if specified as "path/to/file.js:lineNumber"
                source_file = file_path
                if ':' in file_path:
                    source_file = file_path.rsplit(':', 1)[0]
                
                file_entry = {
                    'sourceFile': source_file,
                    'description': metadata,
                }
                files_to_tag.append(file_entry)
        
        logger.info(f"Found {len(files_to_tag)} files to tag")
        return files_to_tag
    
    def get_tagging_instructions(self, file_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tagging instructions for a specific file.
        
        With new actionable_item.json format, tagging instructions come from the metadata object:
        - Source file path
        - Description of what to tag
        - Event type (page_load, click, error)
        - Tracking function to use
        - Specific parameters for LLM
        
        Returns tagging metadata that tells the LLM what to tag
        """
        metadata = file_entry['description']
        
        # Handle both old format (string) and new format (dict)
        if isinstance(metadata, str):
            # Old format: just a description string
            description_text = metadata
            event_type = 'page_load'
            tracking_function = 'trackPageLoad'
            parameters = {}
        else:
            # New format: metadata is a dict with structure:
            # { "description": "...", "eventType": "page_load|click|error", 
            #   "suggestedFunction": "trackPageLoad|trackPageChange|trackPageNotification",
            #   "context": "...", "suggestedParameters": {...} }
            description_text = metadata.get('description', '')
            event_type = metadata.get('eventType', 'page_load')
            
            # Map eventType to suggestedFunction
            func_map = {
                'page_load': 'trackPageLoad',
                'click': 'trackPageChange',
                'error': 'trackPageNotification',
                'navigation': 'trackPageChange',
                'validation': 'trackPageNotification',
                'other': 'trackPageNotification',
            }
            tracking_function = metadata.get('suggestedFunction', func_map.get(event_type, 'trackPageLoad'))
            parameters = metadata.get('suggestedParameters', {})
        
        # Fallback event type detection from description if not specified
        if event_type == 'page_load' and isinstance(metadata, str):
            desc_lower = description_text.lower()
            
            # Check for interaction/click event
            if any(word in desc_lower for word in ['click', 'select', 'submit', 'handle', 'action', 'payment', 'option', 'button', 'navigation']):
                event_type = 'click'
                tracking_function = 'trackPageChange'
            # Check for error event
            elif any(word in desc_lower for word in ['error', 'catch', 'notification', 'alert', 'exception', 'boundary']):
                event_type = 'error'
                tracking_function = 'trackPageNotification'
        
        instructions = {
            'sourceFile': file_entry['sourceFile'],
            'description': description_text,
            'eventType': event_type,
            'trackingFunction': tracking_function,
            'objective': f"Add {event_type} tracking to: {description_text}",
            'taggingFrameworkPath': '../../Tagging',  # Relative path hint
            'parameters': parameters if parameters else self._get_parameters_for_event(event_type, description_text),
        }
        
        return instructions
    
    def _get_parameters_for_event(self, event_type: str, description: str) -> Dict[str, Any]:
        """
        Extract parameters for tracking function based on event type.
        """
        params = {}
        
        if event_type == 'page_load':
            # For page load, extract page name from description
            page_name = description.replace(' - ', ': ').split(':')[0].strip()
            params = {
                'pageName': page_name if page_name else 'Page',
                'flow': 'user-journey',  # Placeholder, LLM should infer
            }
        elif event_type == 'click':
            # For click, extract action name
            selector = description.lower().replace(' ', '-').replace('(', '').replace(')', '')
            params = {
                'selector': selector,
                'message': description,
            }
        elif event_type == 'error':
            # For error, extract event name
            event_name = description.split('(')[0].strip() if '(' in description else description
            params = {
                'eventName': event_name if event_name else 'Error',
                'id': event_name.lower().replace(' ', '-'),
            }
        
        return params
    
    def validate_file_exists(self, source_file: str) -> bool:
        """Check if source file exists in the repo."""
        file_path = self.repo_path / source_file
        exists = file_path.exists()
        
        if not exists:
            logger.warning(f"File not found in repo: {source_file}")
        
        return exists
    
    def generate_tagging_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive tagging report.
        
        Returns:
            Dictionary containing:
            - files_to_tag: List of files needing tagging
            - tagging_instructions: Detailed instructions for each file
            - missing_files: Files referenced but not found
            - summary: Overall tagging plan
        """
        files = self.get_files_to_tag()
        
        report = {
            'spec_file': str(self.json_spec_path),
            'repo_path': str(self.repo_path),
            'tagging_utils_path': str(self.tagging_utils_path),
            'total_files': len(files),
            'files': [],
            'missing_files': [],
            'tagging_summary': {},
        }
        
        for file_entry in files:
            # Check if file exists
            if self.validate_file_exists(file_entry['sourceFile']):
                tagging_inst = self.get_tagging_instructions(file_entry)
                report['files'].append({
                    'file': file_entry['sourceFile'],
                    'description': file_entry['description'],
                    'taggingInstructions': tagging_inst,
                })
            else:
                report['missing_files'].append(file_entry['sourceFile'])
        
        report['tagging_summary'] = {
            'total_files_to_tag': len(report['files']),
            'missing_files_count': len(report['missing_files']),
            'tagging_framework': 'src/pages/ExpressStore/Tagging/ (index.js, dlStructure.js)',
            'tagging_standard': 'Adobe Analytics (eVar, events)',
        }
        
        return report
    
    def get_llm_prompt(self) -> str:
        """
        Generate a comprehensive prompt for the LLM to apply tagging.
        
        Includes:
        - Real code examples from the codebase
        - Exact patterns to follow
        - Event type detection
        - Parameter specifications
        
        Returns:
            A structured prompt that tells the LLM what to tag
        """
        report = self.generate_tagging_report()
        
        prompt = f"""# Vegas Analytics Tagging Agent - Code Generation Task

## Overview
Apply corporate analytics tagging to React components using the **useTagging() custom hook** from the Verizon codebase.

The tagging framework is located at:
- **Framework Path**: `src/pages/ExpressStore/Tagging/`
- **Hook Export**: `index.js` exports `useTagging()`
- **Data Layer**: `dlStructure.js` defines the data structure

## Repository Information
- **Repo Path**: {str(self.repo_path)}
- **Files to Tag**: {report['tagging_summary']['total_files_to_tag']} files
- **Framework**: Custom `useTagging()` hook from `src/pages/ExpressStore/Tagging/index.js`

---

## Task: Apply Tagging to These Files

"""
        # Add each file with enhanced instructions
        for file_info in report['files']:
            tagging_inst = file_info['taggingInstructions']
            event_type = tagging_inst.get('eventType', 'page_load')
            tracking_func = tagging_inst.get('trackingFunction', 'trackPageLoad')
            
            prompt += f"""
### File {len([f for f in report['files'] if report['files'].index(f) <= report['files'].index(file_info)])}
**Path**: `{file_info['file']}`
**Description**: {file_info['description']}
**Event Type**: `{event_type}`
**Function**: `{tracking_func}()`

**What to Track**: {tagging_inst['objective']}

**Parameters to Use**: {tagging_inst['parameters']}

**IMPORTANT**: Use the exact parameters provided above when generating code. Do NOT use generic placeholders like 'Page Name' or 'Flow Name'. Use the specific values provided.

---
"""
        
        prompt += """

## Real Implementation Pattern - EXACT COPY THIS STRUCTURE

### Pattern 1: PAGE LOAD TRACKING

**When to Use**: Component mounts, page becomes visible

**Real Example from Codebase** (`src/pages/ExpressStore/Landing/index.js`):
```javascript
import React, { useEffect } from 'react';
import { useTagging } from '../../Tagging';

function ExpressStore() {
  const { trackPageLoad } = useTagging();
  
  // Other useEffects...
  useEffect(() => {
    // Clear state logic
    dispatch(clearData());
    // ... other dispatches
  }, []);

  // PAGE LOAD TRACKING - Separate useEffect
  useEffect(() => {
    trackPageLoad({ 
      pageName: 'BPK home landing', 
      flow: 'BPK visit' 
    });
  }, []);
  
  return <div>{/* JSX */}</div>;
}
```

**What You Must Generate**:
1. Import: `import { useTagging } from '../../Tagging';`
2. Destructure: `const { trackPageLoad } = useTagging();`
3. Add useEffect:
   ```javascript
   useEffect(() => {
     trackPageLoad({ pageName: '...', flow: '...' });
   }, []);
   ```

---

### Pattern 2: CLICK/INTERACTION TRACKING

**When to Use**: User clicks button, selects option, submits form

**Real Example from Codebase** (`src/pages/ExpressStore/PayBill/index.js`):
```javascript
import { useTagging } from '../../Tagging';

function BillPayPage() {
  const { trackPageChange } = useTagging();
  
  const handlePaymentSelection = (type) => {
    // ADD THIS FIRST:
    trackPageChange(
      'payment-type-selector', 
      `Payment type selected: ${type}`
    );
    
    // THEN EXISTING LOGIC:
    dispatch(setBillType(type));
    mfeLogger(LOG_LEVEL.INFO, { action: 'Paybill_Type_Selected', value: type });
    setCurrentPage('numberPad');
  };
  
  return (
    <button onClick={() => handlePaymentSelection('mobile')}>
      Select Mobile
    </button>
  );
}
```

**What You Must Generate**:
1. Import: `import { useTagging } from '../../Tagging';`
2. Destructure: `const { trackPageChange } = useTagging();`
3. Add to handler (FIRST LINE):
   ```javascript
   trackPageChange('selector-id', 'descriptive message');
   ```

---

### Pattern 3: ERROR TRACKING

**When to Use**: Error occurs, catch block, error boundary

**Real Example from Codebase**:
```javascript
import { useTagging } from '../../Tagging';

function ComponentWithErrorHandling() {
  const { trackPageNotification } = useTagging();
  
  try {
    const response = await fetchBillData();
  } catch (error) {
    // ADD THIS FIRST:
    trackPageNotification(
      'BillFetchError',
      error.message,
      'bill-fetch-error-id'
    );
    
    // THEN EXISTING LOGIC:
    setError('Failed to fetch bill data');
  }
}
```

**What You Must Generate**:
1. Import: `import { useTagging } from '../../Tagging';`
2. Destructure: `const { trackPageNotification } = useTagging();`
3. Add to catch block (FIRST LINE):
   ```javascript
   trackPageNotification('EventName', error.message, 'unique-id');
   ```

---

## Three Tracking Functions - EXACT SIGNATURES

### Function 1: trackPageLoad()
```javascript
trackPageLoad({ 
  pageName: 'string',    // Page/screen identifier (e.g., 'BPK home landing')
  flow: 'string'         // Journey/flow name (e.g., 'BPK visit')
})
```

**Requirements**:
- Called in `useEffect` with `[]` dependency array
- Called ONCE per page/component mount
- Parameters are REQUIRED

### Function 2: trackPageChange()
```javascript
trackPageChange(
  'selector-id',        // CSS selector or element ID (e.g., 'payment-type-selector')
  'message'             // Action description (e.g., 'Payment type selected: mobile')
)
```

**Requirements**:
- Called in event handler (onClick, onChange, onSubmit, etc.)
- Called FIRST in handler before any other logic
- Both parameters are strings

### Function 3: trackPageNotification()
```javascript
trackPageNotification(
  'EventName',          // Event identifier (e.g., 'BillFetchError')
  'message',            // Error message or description
  'unique-id'           // Unique identifier (e.g., 'bill-fetch-error')
)
```

**Requirements**:
- Called in catch blocks or error handlers
- Called FIRST before any other error handling logic
- All three parameters are strings

---

## Import Path Rules - CRITICAL

### Rule 1: Calculate Relative Path Correctly
```
File: src/pages/ExpressStore/PayBill/index.js
Tagging folder: src/pages/ExpressStore/Tagging/

Correct relative path: ../Tagging
✅ CORRECT: import { useTagging } from '../../Tagging';

File: src/pages/ExpressStore/PayBill/PayBillType/index.js
Tagging folder: src/pages/ExpressStore/Tagging/

Correct relative path: ../../Tagging
✅ CORRECT: import { useTagging } from '../../Tagging';
```

### Rule 2: Don't Add /index.js
```
❌ WRONG: import { useTagging } from '../Tagging/index.js';
✅ CORRECT: import { useTagging } from '../../Tagging';
```

---

## Hook Destructuring - IMPORTANT

**Pattern**: Only destructure functions you actually use

### For Page Load Only:
```javascript
const { trackPageLoad } = useTagging();
```

### For Interactions Only:
```javascript
const { trackPageChange } = useTagging();
```

### For Multiple Events:
```javascript
const { trackPageLoad, trackPageChange } = useTagging();
```

**Rule**: Never destructure `trackPageNotification` if not using it

---

## Event Type Detection - HOW TO DECIDE

### This is a PAGE LOAD event if:
- Description mentions: "page", "landing", "home", "screen", "mount", "load", "hub", "view"
- No function name in description
- No line number, or refers to top of component
- → Use `trackPageLoad()` in `useEffect`

### This is a CLICK event if:
- Description mentions: "click", "select", "submit", "handle", "payment", "option", "button", "interaction", "action"
- Description has function name like `handleX()` or method name
- → Use `trackPageChange()` in event handler

### This is an ERROR event if:
- Description mentions: "error", "catch", "validation", "exception", "boundary", "notification", "alert"
- Refers to error handling code
- → Use `trackPageNotification()` in catch block

---

## Validation Checklist - EVERY Generated Change

- [ ] Import added if missing: `import { useTagging } from '../../Tagging';`
- [ ] Relative path is correct (no /index.js)
- [ ] Hook destructured with only needed functions
- [ ] Function called with correct parameters
- [ ] No syntax errors (brackets, commas, quotes balanced)
- [ ] Original code preserved (only added tracking, didn't remove anything)
- [ ] No duplicate imports or tracking calls
- [ ] Parameters are meaningful strings (not generic placeholders)

---

## Error Prevention - Avoid These

❌ **WRONG**: Creating new tagging functions
```javascript
// Don't do this - only use existing hook functions
const myTracker = () => { ... }
```

❌ **WRONG**: Importing with /index.js
```javascript
// Wrong
import { useTagging } from '../Tagging/index.js';
```

❌ **WRONG**: Destructuring all functions when not needed
```javascript
// Wrong
const { trackPageLoad, trackPageChange, trackPageNotification } = useTagging();
// Use only what you need
```

❌ **WRONG**: Modifying existing function logic
```javascript
// Wrong - changed original behavior
const handleClick = (type) => {
  if (!trackPageChange(...)) return;  // Changed logic!
  originalAction();
};

// Right - added tracking, kept original
const handleClick = (type) => {
  trackPageChange(...);
  originalAction();  // Unchanged
};
```

❌ **WRONG**: Adding tracking after error
```javascript
// Wrong
try {
  operation();
  trackPageNotification(...);  // Too late!
} catch (e) {
}

// Right
try {
  operation();
} catch (e) {
  trackPageNotification(...);  // Immediately
  handleError(e);
}
```

---

## Summary: Step-by-Step Generation

1. **Read the description** for each file to tag
2. **Detect event type**: page_load, click, or error?
3. **Find insertion point**: 
   - Page load → In `useEffect` with `[]`
   - Click → In event handler (first line)
   - Error → In catch block (first line)
4. **Calculate import path** from file location to `src/pages/ExpressStore/Tagging/`
5. **Add import** if missing
6. **Destructure hook** with needed functions only
7. **Call tracking function** with meaningful parameters
8. **Preserve all existing code** - only add, never remove

---

## CRITICAL: Use Provided Parameters

For EACH file in the "Task" section:
- Look at the "Parameters to Use" section
- Extract the EXACT VALUES provided:
  - `pageName`: Use this exact value (NOT "Page Name")
  - `flow`: Use this exact value (NOT "Flow Name")
  - `selector`: Use this exact value
  - `message`: Use this exact value
  
**Example:**
If Parameters shows: `{"pageName": "BPK Home Landing", "flow": "BPK visit"}`
Generate: `trackPageLoad({ pageName: 'BPK Home Landing', flow: 'BPK visit' })`

NOT: `trackPageLoad({ pageName: 'Page Name', flow: 'Flow Name' })`

---

## Ready to Generate?

For each file listed in the "Task" section above:
- Apply the correct pattern
- Follow all rules
- **USE THE PROVIDED PARAMETERS EXACTLY**
- Preserve existing code
- Generate correct tagging implementation

Start with the first file and apply the pattern!
"""
        
        if report['missing_files']:
            prompt += f"\n## ⚠️ Missing Files\n\nThese files are referenced but not in repo:\n"
            for missing in report['missing_files']:
                prompt += f"  - `{missing}`\n"
        
        return prompt


# Convenience function for integration
def analyze_tagging_requirements(json_spec_path: str, repo_path: str) -> Dict[str, Any]:
    """
    Analyze tagging requirements from JSON spec.
    
    Args:
        json_spec_path: Path to JSON specification
        repo_path: Path to cloned repository
    
    Returns:
        Tagging analysis report
    """
    applier = TaggingApplier(json_spec_path, repo_path)
    return applier.generate_tagging_report()


def get_tagging_prompt(json_spec_path: str, repo_path: str) -> str:
    """
    Get LLM prompt for tagging application.
    
    Args:
        json_spec_path: Path to JSON specification
        repo_path: Path to cloned repository
    
    Returns:
        Structured prompt for LLM
    """
    applier = TaggingApplier(json_spec_path, repo_path)
    return applier.get_llm_prompt()
