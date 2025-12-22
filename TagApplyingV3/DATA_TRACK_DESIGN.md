# Data-Track Attribute Logic - Design & Implementation

## Overview
This new logic extends the existing tagging system to identify interactive elements (buttons and divs with onClick handlers) in target files and add `data-track` attributes with semantic values extracted from the inner text or label.

## Objectives
1. Analyze target files mentioned in `tagging_report.json`
2. Identify all interactive elements:
   - `<button>` elements
   - `<div>` elements with `onClick` handlers
3. Extract inner text/label from these elements
4. Add `data-track` attribute with the extracted text as value
5. Keep implementation generic (no hardcoding)
6. Use LLM for intelligent element identification and analysis

---

## Approach

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│ DATA-TRACK ATTRIBUTE APPLICATION PIPELINE                │
└──────────────────────────────────────────────────────────┘

INPUT: tagging_report.json (same as main tagging system)
  ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 1: File Analysis                                    │
│ ──────────────────────────────────────────────────────────│
│ For each file in tagging_report.json:                    │
│ 1. Read target file content                              │
│ 2. Extract all interactive elements:                     │
│    • <button> elements (all buttons)                      │
│    • <div onClick={...}> elements                         │
│    • <input onClick={...}> elements                       │
│    • <span onClick={...}> elements                        │
│ 3. For each element: Extract inner text                  │
│ 4. Prepare list of elements for LLM analysis             │
└──────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 2: Element Extraction (Regex/Parsing)               │
│ ──────────────────────────────────────────────────────────│
│ Use regex patterns to find:                              │
│ ┌─ Pattern 1: <button ...>TEXT</button>                  │
│ │  └─ data-track value = TEXT                            │
│ │                                                         │
│ ├─ Pattern 2: <div onClick={handler}>TEXT</div>          │
│ │  └─ data-track value = TEXT                            │
│ │                                                         │
│ ├─ Pattern 3: Dynamic content                            │
│ │  └─ {variableName} → Use LLM to resolve value          │
│ │                                                         │
│ └─ Pattern 4: Nested elements                            │
│    └─ Extract direct text content (children[0] text)     │
└──────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 3: LLM-Driven Smart Enrichment                       │
│ ──────────────────────────────────────────────────────────│
│ For each element found:                                  │
│ 1. Create prompt with:                                  │
│    • Full target file content                            │
│    • Element HTML snippet                                │
│    • Question: "What is the semantic label for this?"    │
│ 2. LLM analyzes:                                         │
│    • Direct text content                                 │
│    • Aria labels (accessibility)                         │
│    • Title attributes                                    │
│    • Placeholder text                                    │
│    • Component names/labels                              │
│ 3. LLM returns sanitized value:                          │
│    {                                                     │
│      "element": "button at line 42",                     │
│      "inner_text": "Submit",                             │
│      "data_track_value": "submit_button",                │
│      "confidence": "high"                                │
│    }                                                     │
└──────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 4: Value Transformation                             │
│ ──────────────────────────────────────────────────────────│
│ Transform extracted text to valid data-track values:     │
│ 1. Cleanup: Trim whitespace, remove extra spaces         │
│ 2. Validation: Check if text is meaningful               │
│ 3. Formatting: kebab-case for consistency                │
│ 4. Length check: Max reasonable length                   │
│ 5. Deduplication: Track unique values                    │
│                                                          │
│ Transformations:                                         │
│ "Submit Form"  → "submit-form"                           │
│ "Click Here"   → "click-here"                            │
│ "Pay Bill"     → "pay-bill"                              │
│ ""             → Skip (empty text)                       │
│ "{variable}"   → LLM resolve or Skip                     │
└──────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 5: Code Generation & Application                    │
│ ──────────────────────────────────────────────────────────│
│ For each element needing data-track:                     │
│ 1. LLM generates updated JSX:                            │
│    OLD: <button onClick={...}>Submit</button>            │
│    NEW: <button data-track="submit"                      │
│                 onClick={...}>Submit</button>            │
│ 2. Placement: Add data-track after opening tag           │
│ 3. Deduplication: Don't add if already present           │
│ 4. Preserve: Keep all other attributes/formatting        │
│ 5. Idempotency: Safe to run multiple times               │
└──────────────────────────────────────────────────────────┘
  ↓
┌──────────────────────────────────────────────────────────┐
│ STEP 6: File Updates & Logging                           │
│ ──────────────────────────────────────────────────────────│
│ 1. Create backup: file.js.datatrack.bak                  │
│ 2. Write updated file with data-track attributes         │
│ 3. Log results to: data_track_report.json                │
│ 4. Track statistics:                                     │
│    • Elements analyzed                                   │
│    • Data-track attributes added                         │
│    • Skipped (already has data-track)                    │
│    • Errors                                              │
└──────────────────────────────────────────────────────────┘
  ↓
OUTPUT: Updated files + data_track_report.json
```

---

## Key Design Decisions

### 1. **Use Same Input Format (actionable_item.json)**
- Read actionable_item.json or accept it as parameter
- Use tagging_report.json as source of files to analyze
- Leverage existing conversion pipeline

### 2. **No Hardcoding - LLM-Driven**
- Don't hardcode regex patterns for value extraction
- Use LLM to intelligently:
  - Identify interactive elements
  - Extract semantic values
  - Generate code with data-track attributes
  - Sanitize values appropriately

### 3. **Multiple Element Types**
- `<button>` - most common interactive element
- `<div onClick={...}>` - custom button-like divs
- `<input onClick={...}>` - input elements with handlers
- `<span onClick={...}>` - text elements with handlers
- `<Link>` - routing components (React Router)

### 4. **Value Extraction Strategies**
```
Strategy 1: Direct Text
<button>Pay Bill</button>
└─ data-track="pay-bill"

Strategy 2: Title/Aria Label
<button title="Submit Payment">
  <Icon />
</button>
└─ data-track="submit-payment"

Strategy 3: Child Text Component
<button>
  <span>Edit Profile</span>
</button>
└─ data-track="edit-profile"

Strategy 4: Dynamic Content (LLM Resolve)
<button onClick={handleClick}>
  {isLoading ? "Saving..." : "Save"}
</button>
└─ data-track="save-button" (LLM determines)

Strategy 5: Component Prop
<CustomButton label="Apply">
└─ data-track="apply" (LLM resolves from prop)
```

### 5. **Value Sanitization**
- Convert to kebab-case for consistency
- Remove HTML/JSX markup
- Trim whitespace
- Max 50 characters
- Allow only alphanumeric + hyphens
- Skip if empty or nonsensical

### 6. **Idempotency**
- Check if data-track already exists
- Skip if present (avoid duplicates)
- Log skipped elements
- Safe to run multiple times

### 7. **Backup Strategy**
- Create .datatrack.bak before modifying
- Store original file content
- Allow rollback if needed

---

## Implementation Components

### Component 1: ElementExtractor
```python
class ElementExtractor:
    """
    Identifies interactive elements in JSX/JS files
    """
    
    def __init__(self, file_path: str, file_content: str):
        self.file_path = file_path
        self.file_content = file_content
    
    def extract_interactive_elements(self) -> List[Dict]:
        """
        Find all interactive elements:
        - <button> elements
        - elements with onClick handlers
        
        Returns:
            List of dicts with:
            - element_type: button | div | input | span | etc.
            - line_number: location in file
            - html_snippet: the full element
            - inner_text: extracted text content
            - has_data_track: already has attribute?
        """
    
    def find_button_elements(self) -> List[Dict]:
        """Find all <button> elements"""
    
    def find_onclick_elements(self) -> List[Dict]:
        """Find all elements with onClick handlers"""
    
    def extract_inner_text(self, element: str) -> str:
        """
        Extract meaningful text from element:
        - Direct text content
        - Title attribute
        - Aria-label attribute
        - Child text nodes
        """
```

### Component 2: ValueGenerator
```python
class ValueGenerator:
    """
    Generates appropriate data-track values
    """
    
    def __init__(self, llm_client: VegasLLMWrapper):
        self.client = llm_client
    
    def generate_value_with_llm(
        self,
        file_content: str,
        element: Dict,
        extracted_text: str
    ) -> str:
        """
        Use LLM to intelligently generate data-track value
        
        LLM analyzes:
        - Element context in file
        - Inner text or labels
        - Surrounding code
        - Component purpose
        
        Returns:
            Sanitized data-track value
        """
    
    def sanitize_value(self, raw_value: str) -> str:
        """
        Clean up generated value:
        - Convert to kebab-case
        - Remove special characters
        - Trim whitespace
        - Max length check
        """
```

### Component 3: CodeApplier
```python
class DataTrackApplier:
    """
    Applies data-track attributes to elements
    """
    
    def __init__(self, llm_client: VegasLLMWrapper):
        self.client = llm_client
    
    def apply_data_track_attributes(
        self,
        file_content: str,
        elements: List[Dict],
        values: Dict[str, str]
    ) -> Tuple[str, List[Dict]]:
        """
        Use LLM to intelligently add data-track attributes
        
        Input:
        - Original file content
        - List of elements to modify
        - Dict of element_id -> data_track_value
        
        Output:
        - Updated file content
        - Log of what was modified
        """
    
    def check_already_has_attribute(
        self,
        element_html: str
    ) -> bool:
        """Check if element already has data-track attribute"""
```

### Component 4: Orchestrator
```python
def apply_data_track_attributes_smart(
    tagging_report_path: str,
    repo_root: str,
    dry_run: bool = False,
    skip_if_already: bool = True
) -> Tuple[int, int, Dict]:
    """
    Main orchestration function
    
    For each file in tagging_report.json:
    1. Extract interactive elements
    2. Generate data-track values (with LLM)
    3. Apply attributes to elements (with LLM)
    4. Write updated files
    5. Log results
    
    Returns:
        (success_count, fail_count, statistics)
    """
```

---

## Data Structures

### Element Record
```python
{
    "file": "src/pages/ExpressStore/PayBill/index.js",
    "element_type": "button",
    "line_number": 42,
    "element_html": '<button onClick={handleSubmit}>Pay Bill</button>',
    "inner_text": "Pay Bill",
    "has_data_track": False,
    "attributes": {
        "onClick": "handleSubmit",
        "className": "btn-primary",
        "type": "submit"
    }
}
```

### Data-Track Mapping
```python
{
    "element_id_line42": {
        "file": "src/pages/ExpressStore/PayBill/index.js",
        "element_type": "button",
        "inner_text": "Pay Bill",
        "data_track_value": "pay-bill",
        "confidence": "high"
    }
}
```

### Report Output (data_track_report.json)
```json
{
    "files_processed": 3,
    "total_elements_found": 15,
    "elements_modified": 12,
    "elements_skipped": 3,
    "files": [
        {
            "file": "src/pages/ExpressStore/PayBill/index.js",
            "status": "success",
            "elements_found": 5,
            "elements_added": 4,
            "elements_skipped": 1,
            "backup_created": true,
            "details": [
                {
                    "line": 42,
                    "element_type": "button",
                    "inner_text": "Pay Bill",
                    "data_track_value": "pay-bill",
                    "status": "added",
                    "reason": null
                }
            ]
        }
    ],
    "statistics": {
        "total_processed": 3,
        "success": 3,
        "failed": 0,
        "buttons_processed": 8,
        "divs_processed": 7,
        "inputs_processed": 0,
        "data_track_attributes_added": 12,
        "data_track_attributes_skipped": 3
    }
}
```

---

## Workflow Integration

### Execution Order
```
1. taggingSuggestion.py          ← Generate tagging_report.json
                                    ↓
2. applyTagging_smart.py         ← Apply tracking code
                                    ↓
3. [NEW] applyDataTrack_smart.py ← Add data-track attributes
                                    ↓
4. Outputs:
   - Updated files with tracking code
   - Updated files with data-track attributes
   - apply_log_smart.json (tracking results)
   - data_track_report.json (data-track results)
```

---

## LLM Prompting Strategy

### Prompt 1: Element Detection
```
You are a React/JSX code analyzer.

## TARGET FILE
[file content]

## TASK
Identify all interactive elements in this React component:
- All <button> elements
- All elements with onClick handlers (div, span, input, etc.)
- All <Link>, <a> routing components

For each element, extract:
1. Element type
2. Line number
3. Full HTML/JSX
4. Inner text or label
5. Whether it already has data-track attribute

Return as JSON array:
[
  {
    "element_type": "button",
    "line": 42,
    "html": "...",
    "inner_text": "Pay Bill",
    "has_data_track": false
  }
]
```

### Prompt 2: Value Generation
```
You are an analytics labeling expert.

## CONTEXT
File: src/pages/.../index.js
Element HTML: <button onClick={...}>Pay Bill</button>
Inner Text: "Pay Bill"

## TASK
Generate an appropriate data-track attribute value for this element.

Consider:
1. What action does this element perform?
2. What is the semantic meaning?
3. Should be concise and descriptive
4. Use kebab-case
5. Max 50 characters
6. Should be self-explanatory

Return JSON:
{
  "data_track_value": "pay-bill",
  "reasoning": "Button submits payment, text is 'Pay Bill'",
  "confidence": "high"
}
```

### Prompt 3: Code Application
```
You are a code transformation expert.

## FRAMEWORK RULES
- Add data-track attribute to interactive elements
- Place after opening tag
- Format: data-track="kebab-case-value"
- Preserve all existing code
- No other changes

## FILE
[original file content]

## MODIFICATIONS NEEDED
[
  {
    "line": 42,
    "element_type": "button",
    "data_track_value": "pay-bill"
  },
  {
    "line": 65,
    "element_type": "div",
    "data_track_value": "close-modal"
  }
]

## TASK
Apply data-track attributes to specified elements.
Return updated file content as valid JSX/JavaScript.
```

---

## Error Handling

### Element Detection Failures
- Log: "Could not parse element at line X"
- Action: Skip element, continue with others
- Reason: Complex JSX syntax, nested JSX, etc.

### LLM Generation Failures
- Log: "LLM failed to generate value for element at line X"
- Action: Use extracted text as fallback
- Fallback: Sanitize inner_text as data-track value

### File Write Failures
- Log: "Could not write to file X"
- Action: Keep backup, don't overwrite original
- Safety: Never lose original file

### Backup Failures
- Log: "Could not create backup"
- Action: Abort write, leave original untouched
- Safety: Better to not modify than to risk data loss

---

## Testing Strategy

### Unit Tests
- Element extraction (regex accuracy)
- Value sanitization (kebab-case conversion)
- Idempotency (no duplicates)
- Backup creation and restoration

### Integration Tests
- Full pipeline with sample files
- LLM response handling
- File writing and recovery
- Report generation accuracy

### Sample Test File
```javascript
// Before
function PayBillPage() {
  return (
    <div>
      <button onClick={handleSubmit}>Pay Bill</button>
      <div onClick={closeModal}>Close</div>
      <button>Cancel</button>
    </div>
  );
}

// After
function PayBillPage() {
  return (
    <div>
      <button data-track="pay-bill" onClick={handleSubmit}>Pay Bill</button>
      <div data-track="close-modal" onClick={closeModal}>Close</div>
      <button data-track="cancel">Cancel</button>
    </div>
  );
}
```

---

## Summary

The data-track attribute logic:
✅ Uses same input (actionable_item.json) as main system
✅ Analyzes files from tagging_report.json
✅ Identifies all interactive elements without hardcoding
✅ Uses LLM to intelligently extract and generate values
✅ Applies attributes safely with backups
✅ Provides detailed reporting
✅ Maintains idempotency
✅ Integrates seamlessly with existing pipeline
