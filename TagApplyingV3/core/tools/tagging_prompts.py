"""
Tagging Prompt Templates for LLM

This module provides specialized prompts for different tagging scenarios
based on real manual tagging patterns from the codebase.
"""

# ============================================================
# PAGE LOAD TRACKING PROMPT
# ============================================================

PAGE_LOAD_PROMPT_TEMPLATE = """
## Task: Add Page Load Tracking

You need to add page load tracking to a React component.

### Real Pattern from Codebase
```javascript
import React, { useEffect } from 'react';
import { useTagging } from '../Tagging';

function ExpressStore() {
  const { trackPageLoad } = useTagging();
  
  useEffect(() => {
    trackPageLoad({ 
      pageName: 'BPK home landing', 
      flow: 'BPK visit' 
    });
  }, []);
  
  return (/* JSX */);
}
```

### What to Generate

1. **Import** (if not already present):
   ```javascript
   import { useTagging } from '../Tagging';
   ```
   
   Note: Calculate correct relative path from file location to `src/pages/ExpressStore/Tagging/`

2. **Inside component function, add hook call**:
   ```javascript
   const { trackPageLoad } = useTagging();
   ```

3. **Add useEffect for tracking** (place after other useEffects):
   ```javascript
   useEffect(() => {
     trackPageLoad({ 
       pageName: '{PAGE_NAME}',
       flow: '{FLOW_NAME}'
     });
   }, []);
   ```

### Parameters
- **FILE**: {FILE}
- **PAGE_NAME**: {PAGE_NAME} (from description or infer from component)
- **FLOW_NAME**: {FLOW_NAME} (from description or infer from flow context)

### Rules
- Only add tracking call if not already present
- Use meaningful page/flow names (short, clear strings)
- Place useEffect separately from other effects
- Don't modify existing code, only add tracking
- Ensure import path is correct (use ../ or ../../ based on file depth)

### Output
Return JSON:
```json
{{
  "applied": true/false,
  "reason": "explanation",
  "updated_file": "full file text with tracking added"
}}
```
"""

# ============================================================
# CLICK/INTERACTION TRACKING PROMPT
# ============================================================

CLICK_TRACKING_PROMPT_TEMPLATE = """
## Task: Add Click/Interaction Tracking

You need to add user interaction (click, selection, submission) tracking to a React component.

### Real Pattern from Codebase
```javascript
import React from 'react';
import { useTagging } from '../Tagging';

function BillPayPage() {
  const { trackPageChange } = useTagging();
  
  const handlePaymentSelection = (type) => {
    // ADD TRACKING HERE (FIRST LINE):
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

### What to Generate

1. **Import** (if not already present):
   ```javascript
   import { useTagging } from '../Tagging';
   ```

2. **Inside component, add hook call**:
   ```javascript
   const { trackPageChange } = useTagging();
   ```

3. **In the event handler (line {LINE_NUMBER}), add as FIRST statement**:
   ```javascript
   trackPageChange('{SELECTOR}', '{MESSAGE}');
   ```

### Parameters
- **FILE**: {FILE}
- **LINE_NUMBER**: {LINE_NUMBER} (approximate location of handler)
- **HANDLER_NAME**: {HANDLER_NAME} (e.g., 'handlePaymentSelection')
- **SELECTOR**: {SELECTOR} (CSS selector or unique ID, use kebab-case)
- **MESSAGE**: {MESSAGE} (describe the action, can use variables)

### Rules
- Find the exact event handler at/near the line number
- Add tracking as the VERY FIRST line in the handler
- Use meaningful selector and message
- Don't modify existing handler logic, only add tracking above it
- Ensure import path is correct
- Don't add tracking if already present

### Example Selector Names
- `payment-type-selector` (for payment selection)
- `login-option-button` (for login choices)
- `complete-order-submit` (for form submission)
- `navigation-back-button` (for navigation)

### Output
Return JSON:
```json
{{
  "applied": true/false,
  "reason": "explanation",
  "updated_file": "full file text with tracking added"
}}
```
"""

# ============================================================
# ERROR TRACKING PROMPT
# ============================================================

ERROR_TRACKING_PROMPT_TEMPLATE = """
## Task: Add Error/Notification Tracking

You need to add error or notification tracking to a React component's error handler.

### Real Pattern from Codebase
```javascript
import React from 'react';
import { useTagging } from '../Tagging';

function ComponentWithErrorHandling() {
  const { trackPageNotification } = useTagging();
  
  try {
    const response = await fetchBillData();
    // ... processing
  } catch (error) {
    // ADD TRACKING HERE (FIRST LINE):
    trackPageNotification(
      'BillFetchError',
      error.message,
      'bill-fetch-error'
    );
    
    // THEN EXISTING ERROR LOGIC:
    setError('Failed to fetch bill data');
    logger.error(error);
  }
}
```

### What to Generate

1. **Import** (if not already present):
   ```javascript
   import { useTagging } from '../Tagging';
   ```

2. **Inside component, add hook call**:
   ```javascript
   const { trackPageNotification } = useTagging();
   ```

3. **In the catch block (line {LINE_NUMBER}), add as FIRST statement**:
   ```javascript
   trackPageNotification('{EVENT_NAME}', error.message, '{ID}');
   ```

### Parameters
- **FILE**: {FILE}
- **LINE_NUMBER**: {LINE_NUMBER} (approximate location of catch block)
- **EVENT_NAME**: {EVENT_NAME} (e.g., 'BillFetchError', 'ValidationError')
- **ID**: {ID} (unique identifier, use kebab-case)

### Rules
- Find the catch block at/near the line number
- Add tracking as the VERY FIRST line in the catch block
- Event name should be descriptive and PascalCase
- ID should be kebab-case version of event name
- Don't modify existing error handling logic, only add tracking above it
- Ensure import path is correct
- Don't add tracking if already present

### Example Event Names
- `BillFetchError` (for API failures)
- `ValidationError` (for form validation)
- `AuthenticationError` (for auth failures)
- `ComponentError` (for error boundaries)

### Output
Return JSON:
```json
{{
  "applied": true/false,
  "reason": "explanation",
  "updated_file": "full file text with tracking added"
}}
```
"""

# ============================================================
# VALIDATION PROMPT
# ============================================================

VALIDATION_PROMPT_TEMPLATE = """
## Task: Validate Tagging Implementation

Verify that the tagging code is correctly implemented.

### Validation Checklist

Check each of these:

1. **Import Statement**
   - [ ] `import { useTagging } from '../Tagging';` is present
   - [ ] Relative path is correct (no `/index.js` at end)
   - [ ] Not importing from wrong location

2. **Hook Destructuring**
   - [ ] `useTagging()` is called in component
   - [ ] Only needed functions are destructured
   - [ ] Examples: `const {{ trackPageLoad }} = useTagging();`

3. **Page Load Tracking** (if applicable)
   - [ ] `useEffect` hook is present with empty dependency array `[]`
   - [ ] `trackPageLoad()` called with `{{ pageName: '...', flow: '...' }}`
   - [ ] Both parameters are strings (not undefined/null)

4. **Click Tracking** (if applicable)
   - [ ] `trackPageChange()` called in event handler
   - [ ] Called as FIRST statement in handler
   - [ ] Both parameters are strings
   - [ ] Example: `trackPageChange('selector-id', 'message')`

5. **Error Tracking** (if applicable)
   - [ ] `trackPageNotification()` called in catch block
   - [ ] Called as FIRST statement in catch
   - [ ] Three parameters all strings
   - [ ] Example: `trackPageNotification('ErrorName', error.message, 'id')`

6. **Code Integrity**
   - [ ] No syntax errors
   - [ ] All brackets/parentheses/quotes balanced
   - [ ] Original code preserved (not removed)
   - [ ] No duplicate imports

7. **Quality Checks**
   - [ ] Parameters are meaningful (not generic/placeholder)
   - [ ] No console.log or debugging code left
   - [ ] Follows React best practices

### Output
Return validation result:
```json
{{
  "valid": true/false,
  "errors": ["list of any validation errors"],
  "warnings": ["list of any warnings"],
  "suggestions": ["list of improvements if any"]
}}
```
"""

# ============================================================
# COMPLETE TAGGING WORKFLOW PROMPT
# ============================================================

COMPLETE_WORKFLOW_PROMPT = """
## Complete Vegas Analytics Tagging Workflow

### Overview
Apply analytics tagging to React components using the `useTagging()` hook from the Verizon codebase.

### Framework Information
- **Location**: `src/pages/ExpressStore/Tagging/`
- **Hook Export**: `useTagging()` from `index.js`
- **Data Layer**: Defined in `dlStructure.js`

### Three Tracking Functions

1. **trackPageLoad()** - Page/Component Mount
   ```javascript
   trackPageLoad({ pageName: 'string', flow: 'string' })
   ```
   - Called in `useEffect` with `[]` dependency
   - Once per page load
   
2. **trackPageChange()** - User Interactions
   ```javascript
   trackPageChange('selector', 'message')
   ```
   - Called in event handlers
   - First line of handler
   
3. **trackPageNotification()** - Errors
   ```javascript
   trackPageNotification('EventName', error.message, 'id')
   ```
   - Called in catch blocks
   - First line of catch

### Step-by-Step Generation Process

For each file to tag:

1. **Determine Event Type**
   - Keywords 'page', 'landing', 'load', 'mount' → Page Load
   - Keywords 'click', 'select', 'submit', 'handle' → Click/Interaction
   - Keywords 'error', 'catch', 'validation' → Error
   
2. **Calculate Import Path**
   - From: `src/pages/ExpressStore/PayBill/index.js`
   - To: `src/pages/ExpressStore/Tagging/`
   - Path: `../Tagging`
   
3. **Add Import** (if missing)
   ```javascript
   import { useTagging } from '../Tagging';
   ```
   
4. **Destructure Hook** (only what's needed)
   ```javascript
   const { trackPageLoad } = useTagging();
   ```
   
5. **Add Tracking** (based on event type)
   - Page Load: Add useEffect
   - Click: Add to handler (first line)
   - Error: Add to catch block (first line)
   
6. **Use Meaningful Parameters**
   - Page names: 'Bill Payment Page', 'Landing Hub'
   - Flow names: 'pay-bill-mobile', 'account-access'
   - Selectors: 'payment-type-selector', 'login-option'
   - Messages: 'Payment type selected: mobile'

7. **Validate**
   - No syntax errors
   - Correct import path
   - Meaningful parameters
   - Original code preserved

### Real Examples

**Page Load**:
```javascript
import { useTagging } from '../Tagging';

function Landing() {
  const { trackPageLoad } = useTagging();
  
  useEffect(() => {
    trackPageLoad({ pageName: 'Landing', flow: 'visit' });
  }, []);
}
```

**Click Tracking**:
```javascript
import { useTagging } from '../Tagging';

function PayBill() {
  const { trackPageChange } = useTagging();
  
  const handleClick = (type) => {
    trackPageChange('payment-selector', `Selected: ${type}`);
    // ... original logic
  };
}
```

**Error Tracking**:
```javascript
import { useTagging } from '../Tagging';

function Fetch() {
  const { trackPageNotification } = useTagging();
  
  try {
    // ... operation
  } catch (error) {
    trackPageNotification('FetchError', error.message, 'fetch-err');
    // ... error handling
  };
}
```

### Ready to Generate!

Apply the correct pattern for each file listed.
"""

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_prompt_for_event_type(event_type: str, **kwargs) -> str:
    """
    Get the appropriate prompt template for the event type.
    
    Args:
        event_type: 'page_load', 'click', 'error', 'validate', or 'complete'
        **kwargs: Template variables to substitute
        
    Returns:
        Formatted prompt template
    """
    templates = {
        'page_load': PAGE_LOAD_PROMPT_TEMPLATE,
        'click': CLICK_TRACKING_PROMPT_TEMPLATE,
        'error': ERROR_TRACKING_PROMPT_TEMPLATE,
        'validate': VALIDATION_PROMPT_TEMPLATE,
        'complete': COMPLETE_WORKFLOW_PROMPT,
    }
    
    template = templates.get(event_type, COMPLETE_WORKFLOW_PROMPT)
    
    # Substitute variables
    for key, value in kwargs.items():
        template = template.replace('{' + key + '}', str(value))
    
    return template


def get_system_prompt() -> str:
    """
    Get the system prompt for the LLM.
    
    Returns:
        System prompt defining the LLM's role
    """
    return """You are an expert React code generation assistant specializing in analytics tagging.

Your task is to add Vegas Analytics tracking to React components using the useTagging() hook.

## Core Responsibilities
1. Identify the correct tagging pattern (page load, click, or error)
2. Calculate correct import paths
3. Add tracking code that preserves existing functionality
4. Ensure code quality and adherence to patterns

## Key Principles
- Only add tracking code, never modify existing logic
- Use the three provided functions: trackPageLoad, trackPageChange, trackPageNotification
- Calculate relative paths correctly (no /index.js at end)
- Destructure only functions actually needed
- Provide meaningful, descriptive parameters
- Always return valid JSON

## Error Handling
- If tracking already exists, return unchanged file with reason
- If import path cannot be determined, request clarification
- If handler cannot be located, provide helpful error message

## Output Format
Always return valid JSON:
{
  "applied": boolean,
  "reason": "explanation",
  "updated_file": "full file content"
}
"""


def get_user_prompt_for_file(file_path: str, description: str, event_type: str, 
                            parameters: dict = None) -> str:
    """
    Get the user prompt for a specific file.
    
    Args:
        file_path: Path to file to tag
        description: What to tag
        event_type: 'page_load', 'click', or 'error'
        parameters: Additional parameters for the tagging
        
    Returns:
        User prompt for this specific file
    """
    params = parameters or {}
    
    prompt = f"""## File to Tag

**Path**: {file_path}
**Description**: {description}
**Event Type**: {event_type}

### Parameters
"""
    
    for key, value in params.items():
        prompt += f"- **{key}**: {value}\n"
    
    prompt += f"""

### Instructions
Apply the {event_type} tracking pattern to this file.

Use the guidelines and examples provided in the system prompt.

Ensure:
1. Correct import path
2. Hook properly destructured
3. Tracking called with meaningful parameters
4. All existing code preserved
5. No syntax errors

Return JSON with the updated file.
"""
    
    return prompt
