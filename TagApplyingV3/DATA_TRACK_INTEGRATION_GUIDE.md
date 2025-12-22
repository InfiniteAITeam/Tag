# Data-Track Attribute System - Integration Guide

## Quick Start

### What This Does
Automatically adds `data-track` attributes to interactive elements (buttons, divs with onClick) in your React components. Uses LLM to intelligently extract semantic values from button text and labels.

### The Workflow

```
1. actionable_item.json
   ↓ (taggingSuggestion.py)
2. tagging_report.json
   ↓ (applyTagging_smart.py)
3. Files updated with tracking code
   ↓ (applyDataTrack_smart.py) ← NEW
4. Files updated with data-track attributes
```

---

## Setup & Configuration

### Prerequisites
1. Python 3.8+
2. Vegas LLM API access (for intelligent analysis)
3. Repository cloned locally
4. actionable_item.json with file specifications

### Environment Variables
Add to your `.env` file:

```bash
# Existing (for tracking tagging)
VEGAS_API_KEY=your_api_key_here
context_name=your_context
usecase_name=your_usecase
REPO_URL=https://github.com/your/repo.git
CLONE_LOCAL=cloned_repo

# Optional (for data-track)
# Uses same configuration as tracking tagging
```

---

## Execution Flow

### Full Pipeline

```bash
# Step 1: Generate tagging report (files to analyze)
python core/taggingSuggestion.py

# Step 2: Apply tracking code (trackPageLoad, etc.)
python core/applyTagging_smart.py

# Step 3: Apply data-track attributes ← NEW
python core/applyDataTrack_smart.py
```

### Or Just Data-Track Attributes

If you only want to add data-track attributes (without tracking code):

```bash
# Step 1: Generate tagging report (provides file list)
python core/taggingSuggestion.py

# Step 3: Apply data-track attributes directly
python core/applyDataTrack_smart.py
```

---

## File Structure

```
core/
├── applyDataTrack_smart.py          ← NEW: Main orchestration script
├── tools/
│   ├── data_track_extractor.py      ← NEW: Element identification
│   ├── data_track_applier.py        ← NEW: LLM-driven application
│   ├── vegas_llm_utils.py           (existing)
│   └── ...
└── outputs/
    ├── tagging_report.json          (existing)
    ├── apply_log_smart.json         (existing)
    └── data_track_report.json       ← NEW: Data-track results
```

---

## Module Overview

### 1. `data_track_extractor.py`

**Purpose**: Identify interactive elements in React/JSX files

**Main Classes**:

#### ElementExtractor
```python
extractor = ElementExtractor(file_path, file_content)
elements = extractor.extract_all_interactive_elements()

# Returns: List[InteractiveElement]
# Each element contains:
#   - element_type: button | div | span | input | link
#   - line_number: Where in file
#   - inner_text: Button text or label
#   - attributes: className, onClick, title, etc.
#   - has_data_track: Already has attribute?
```

#### ValueSanitizer
```python
# Convert raw text to valid data-track value
value = ValueSanitizer.sanitize("Pay Bill")
# Returns: "pay-bill"

# Check if value is valid
is_valid = ValueSanitizer.is_valid_value("pay-bill")
# Returns: True

# Extract meaningful text from element
text = ValueSanitizer.extract_text_from_element(element)
# Returns: Inner text, aria-label, title, etc.
```

**Element Detection**:
- `<button>` elements: All buttons
- `<div onClick={...}>`: Custom buttons
- `<span onClick={...}>`: Clickable text
- `<input onClick={...}>`: Input elements with handlers
- `<Link>` components: React Router links

---

### 2. `data_track_applier.py`

**Purpose**: Use LLM to intelligently generate and apply data-track attributes

**Main Classes**:

#### DataTrackPromptBuilder
Builds context-aware prompts for LLM:

```python
# 1. Element Detection Prompt
prompt = DataTrackPromptBuilder.build_element_detection_prompt(
    file_content,
    file_path
)
# Asks LLM to identify all interactive elements

# 2. Value Generation Prompt
prompt = DataTrackPromptBuilder.build_value_generation_prompt(
    file_content,
    file_path,
    element,
    extracted_text
)
# Asks LLM to generate appropriate data-track value

# 3. Code Application Prompt
prompt = DataTrackPromptBuilder.build_code_generation_prompt(
    file_content,
    file_path,
    elements_to_modify
)
# Asks LLM to apply attributes to code
```

#### DataTrackApplier
```python
client = VegasLLMWrapper()
applier = DataTrackApplier(client)

# Detect elements using LLM
elements = applier.detect_elements_with_llm(file_content, file_path)

# Generate value for element
value, reasoning, confidence = applier.generate_value_with_llm(
    file_content,
    file_path,
    element,
    extracted_text
)

# Apply data-track attributes
updated_content, log = applier.apply_data_track_with_llm(
    file_content,
    file_path,
    elements_to_modify
)
```

---

### 3. `applyDataTrack_smart.py`

**Purpose**: Orchestrate entire data-track attribute application process

**Main Function**:
```python
def apply_data_track_attributes_smart(
    tagging_report_path: str,      # Path to tagging_report.json
    repo_root: str,                # Repository root
    use_llm: bool = True,          # Use LLM for intelligent analysis
    dry_run: bool = False,         # Simulate without writing
    skip_if_already: bool = True   # Skip if already has data-track
) -> Tuple[int, int, Dict]:
    """
    Returns: (success_count, fail_count, statistics)
    """
```

**Workflow Per File**:
```
1. Read file from tagging_report.json
2. Extract interactive elements
3. For each element:
   a. Check if already has data-track
   b. If not, generate value using LLM
   c. Validate generated value
4. Apply all data-track attributes with LLM
5. Create backup (.datatrack.bak)
6. Write updated file
7. Log results
```

---

## How It Works (No Hardcoding)

### Step 1: Element Detection (Regex-based)
```python
# ElementExtractor uses patterns to find elements
# Pattern: <button ...>TEXT</button>
# Pattern: <div onClick={...}>TEXT</div>
# Pattern: <span onClick={...}>TEXT</span>

elements = extractor.extract_all_interactive_elements()
# Returns list of found elements with their properties
```

### Step 2: Value Generation (LLM-driven)
```python
# For each element, create LLM prompt:
prompt = f"""
FILE CONTENT: [full file]
ELEMENT: <button>Pay Bill</button>
EXTRACTED TEXT: "Pay Bill"

Generate appropriate data-track value.
Should be semantic, kebab-case, max 50 chars.
Return JSON with: data_track_value, reasoning, confidence
"""

response = llm.invoke(prompt)
# LLM returns: {"data_track_value": "pay-bill", ...}
```

### Step 3: Code Application (LLM-driven)
```python
# For each element to modify, create prompt:
prompt = f"""
FILE: [original file content]
MODIFICATIONS: [list of line number + value mappings]

Add data-track attributes to specified elements.
Place after opening tag.
Preserve all other code exactly.
Return complete updated file.
"""

response = llm.invoke(prompt)
# LLM returns: Complete updated file with data-track attributes
```

### Step 4: Safety & Idempotency
```python
# Check if element already has data-track
if elem.has_data_track:
    if skip_if_already:
        skip_element()  # Don't add duplicate
    
# Create backup before writing
backup_file = file.with_suffix(file.suffix + ".datatrack.bak")

# Write updated file
write_file(file, updated_content)
```

---

## Value Transformation Examples

```
Input Element                          Data-Track Value
────────────────────────────────────  ─────────────────
<button>Pay Bill</button>              pay-bill
<button>Submit Payment</button>        submit-payment
<div onClick={close}>Close Modal</div> close-modal
<button title="Edit">
  <EditIcon />
</button>                              edit
<span onClick={nav}>Dashboard</span>   dashboard
<button>Sign In</button>               sign-in
<input onClick={select}>Select</input> select
```

**Transformation Rules**:
1. Extract inner text, title, aria-label, or placeholder
2. Convert to lowercase
3. Replace spaces/underscores with hyphens
4. Remove special characters
5. Limit to 50 characters
6. Kebab-case validation

---

## Output Files

### data_track_report.json

Located at: `core/outputs/data_track_report.json`

```json
{
  "logs": [
    {
      "file": "src/pages/ExpressStore/PayBill/index.js",
      "status": "success",
      "elements_found": 5,
      "elements_modified": 4,
      "elements_skipped": 1,
      "details": [
        {
          "line": 42,
          "element_type": "button",
          "data_track_value": "pay-bill",
          "confidence": "high",
          "status": "modified"
        },
        {
          "line": 65,
          "element_type": "div",
          "data_track_value": "close-modal",
          "confidence": "high",
          "status": "modified"
        },
        {
          "line": 80,
          "element_type": "button",
          "status": "skipped",
          "reason": "Already has data-track attribute"
        }
      ]
    }
  ],
  "stats": {
    "total_files": 3,
    "processed": 3,
    "success": 3,
    "failed": 0,
    "total_elements_found": 15,
    "total_elements_modified": 12,
    "total_elements_skipped": 3,
    "backup_created": 3
  }
}
```

### Backup Files

Original files are backed up before modification:
- Original: `PayBill/index.js`
- Backup: `PayBill/index.js.datatrack.bak`

Allows rollback if needed.

---

## Error Handling

### File Errors
```
File Not Found
├─ Check file path in tagging_report.json
└─ Verify repository is cloned

File Read Failed
├─ Check file permissions
└─ Verify file is valid UTF-8
```

### LLM Errors
```
LLM Request Failed
├─ Check VEGAS_API_KEY is set
├─ Verify network connectivity
└─ Check LLM service status

LLM Response Invalid
├─ LLM may return malformed JSON
├─ Fallback: Skip element or use default
└─ Logged in data_track_report.json
```

### Element Detection
```
No Elements Found
├─ File may not have interactive elements
├─ Check file has buttons or onClick handlers
└─ Logged in data_track_report.json

Value Generation Failed
├─ LLM couldn't generate appropriate value
├─ Fallback: Sanitize extracted text
└─ Logged with low confidence
```

### Write Errors
```
Backup Failed
├─ Abort write (don't overwrite)
├─ Check disk space
└─ Check file permissions

File Write Failed
├─ Original file remains unchanged
├─ Backup created before write
└─ Check disk space and permissions
```

---

## Integration with Existing System

### Using Output from tagging_report.json

The system reads the same `tagging_report.json` generated by `taggingSuggestion.py`:

```python
# tagging_report.json structure
{
  "files": [
    {
      "file": "src/pages/ExpressStore/PayBill/PayBillType/index.js",
      "description": {...},
      "taggingInstructions": {...}
    }
  ]
}

# applyDataTrack_smart.py uses:
files = tagging_report["files"]

# For each file:
file_path = file_info["file"]
# ... analyze for interactive elements
```

### Workflow with Both Systems

```
Step 1: Generate Report
┌─ python core/taggingSuggestion.py
└─ Output: tagging_report.json

Step 2: Apply Tracking Code (Optional)
┌─ python core/applyTagging_smart.py
├─ Input: tagging_report.json
├─ Adds: import, useTagging hook, trackPageLoad call
└─ Output: apply_log_smart.json

Step 3: Apply Data-Track Attributes
┌─ python core/applyDataTrack_smart.py
├─ Input: tagging_report.json (same file)
├─ Analyzes same files from tagging_report.json
├─ Adds: data-track attributes to interactive elements
└─ Output: data_track_report.json

Result: Files with BOTH:
├─ Tracking code (trackPageLoad, trackPageChange)
└─ Data-track attributes on interactive elements
```

---

## Usage Examples

### Example 1: Full Pipeline

```bash
# Clone repo and analyze files
python core/taggingSuggestion.py

# Add tracking code
python core/applyTagging_smart.py

# Add data-track attributes
python core/applyDataTrack_smart.py

# Check results
cat core/outputs/data_track_report.json
```

### Example 2: Data-Track Only

If you only want to add data-track attributes:

```bash
# Step 1: Generate report (identifies files)
python core/taggingSuggestion.py

# Step 3: Skip tracking code, go straight to data-track
python core/applyDataTrack_smart.py
```

### Example 3: Dry Run

Test without modifying files:

```python
# In applyDataTrack_smart.py, use:
success, fail, stats = apply_data_track_attributes_smart(
    tagging_report_path=report_file,
    repo_root=repo_path,
    use_llm=True,
    dry_run=True,  # ← Don't write files
    skip_if_already=True
)
```

### Example 4: Fallback Mode (No LLM)

Run without Vegas LLM (less intelligent but functional):

```bash
# Just unset or don't set VEGAS_API_KEY
unset VEGAS_API_KEY

# Run script - will use fallback mode
python core/applyDataTrack_smart.py
```

---

## Advanced Configuration

### Custom Repository Path

```bash
# In .env
CLONE_LOCAL=/path/to/your/repo
REPO_URL=https://github.com/your/repo.git
```

### Skip Already Tagged Elements

```python
# In code
success, fail, stats = apply_data_track_attributes_smart(
    tagging_report_path=report_file,
    repo_root=repo_path,
    skip_if_already=True,  # Don't add if already has data-track
)
```

---

## Troubleshooting

### "No files found in tagging_report.json"
- Run `taggingSuggestion.py` first
- Check `actionable_item.json` has valid file paths
- Verify repository was cloned successfully

### "Interactive elements found but values look wrong"
- Check LLM is enabled (VEGAS_API_KEY set)
- Review generated values in data_track_report.json
- LLM confidence score indicates certainty

### "LLM errors in logs"
- Verify VEGAS_API_KEY is correct
- Check network connectivity
- Review LLM response format in debug output

### "Files modified but attributes look wrong"
- Check backup file (.datatrack.bak)
- Review exact changes in data_track_report.json
- Re-run to see what was skipped

---

## Testing

### Sample Test File

```javascript
// Before
function PaymentPage() {
  return (
    <div>
      <button onClick={handleSubmit}>
        Pay Bill
      </button>
      <div onClick={closeModal}>
        Close
      </div>
      <button className="cancel">
        Cancel
      </button>
    </div>
  );
}

// After (with data-track attributes)
function PaymentPage() {
  return (
    <div>
      <button data-track="pay-bill" onClick={handleSubmit}>
        Pay Bill
      </button>
      <div data-track="close-modal" onClick={closeModal}>
        Close
      </div>
      <button data-track="cancel" className="cancel">
        Cancel
      </button>
    </div>
  );
}
```

---

## Performance Notes

### Processing Time
- Small file (< 1000 lines): ~2-5 seconds
- Medium file (1000-5000 lines): ~5-15 seconds
- Large file (> 5000 lines): ~15-30 seconds

Time includes:
- File reading
- Element extraction (regex)
- LLM API calls (main cost)
- Code generation
- File writing and backup

### Optimization Tips
1. Use `skip_if_already=True` to skip already-tagged files
2. Batch process: Use same LLM client for all files
3. Monitor API rate limits with Vegas LLM

---

## Security & Safety

✅ **Backups Created**: `.datatrack.bak` files allow rollback
✅ **No Eval/Exec**: All LLM output validated as JSON
✅ **Read-Only Verification**: Checks file exists before reading
✅ **Atomic Writes**: Backup before any modification
✅ **Dry-Run Mode**: Test without making changes
✅ **Idempotent**: Safe to run multiple times

---

## Summary

The data-track attribute system:
- ✅ Uses same input as tracking tagging system
- ✅ Identifies interactive elements automatically
- ✅ Generates semantic values using LLM
- ✅ Applies attributes safely with backups
- ✅ Provides detailed reporting
- ✅ No hardcoding - fully LLM-driven
- ✅ Integrates seamlessly with existing pipeline
