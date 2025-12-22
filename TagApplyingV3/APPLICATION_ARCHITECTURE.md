# Smart Tagging Application - Architecture & Workflow Analysis

## Overview
This is an **LLM-Aware Smart Tagging System** that automatically applies analytics tracking tags to React components. It uses Vegas LLM to intelligently understand the codebase structure and add tracking functions without hardcoding.

---

## Application Architecture

### 1. **System Components**

```
┌─────────────────────────────────────────────────────────────┐
│                    TAGGING PIPELINE                         │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ STAGE 1: INPUT & ANALYSIS                                        │
│ ──────────────────────────────────────────────────────────────── │
│                                                                  │
│  Input: actionable_item.json                                    │
│  └─ List of React components to tag                             │
│  └─ Each entry contains:                                        │
│     • file: path to React component                             │
│     • description: What to track                                │
│     • eventType: page_load | click | error                      │
│     • suggestedFunction: trackPageLoad | trackPageChange        │
│     • suggestedParameters: eVar, event values, etc.             │
│                                                                  │
│  Process: taggingSuggestion.py                                  │
│  └─ Clones repository from REPO_URL                             │
│  └─ Analyzes each file against JSON spec                        │
│  └─ Generates: tagging_report.json                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ STAGE 2: REPORT GENERATION                                       │
│ ──────────────────────────────────────────────────────────────── │
│                                                                  │
│  Output: tagging_report.json                                    │
│  └─ Contains files found from actionable_item.json              │
│  └─ Each file entry includes:                                   │
│     • file: src/pages/ExpressStore/PayBill/index.js             │
│     • description: Full metadata from actionable_item.json       │
│     • taggingInstructions: Line numbers, tracking functions     │
│                                                                  │
│  Framework Detection:                                           │
│  └─ Locates Tagging framework at:                               │
│     src/pages/ExpressStore/Tagging/index.js                    │
│  └─ Reads available tracking functions (trackPageLoad, etc.)    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ STAGE 3: SMART CONVERSION                                        │
│ ──────────────────────────────────────────────────────────────── │
│                                                                  │
│  Process: applyTagging_smart.py                                 │
│  └─ convert_report_to_apply_format()                            │
│  └─ Converts tagging_report.json → apply_plan_smart.json        │
│                                                                  │
│  Output Format: apply_plan_smart.json                           │
│  └─ Flat array of items with fields:                            │
│     • file: absolute path to target file                        │
│     • file_path: relative path in repo                          │
│     • action: page_load | click | error                         │
│     • event: trackPageLoad | trackPageChange                    │
│     • suggested_params: Analytics parameters                    │
│     • top_match: { line: N } - anchor point                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ STAGE 4: LLM-DRIVEN INTELLIGENT APPLICATION                      │
│ ──────────────────────────────────────────────────────────────── │
│                                                                  │
│  Process: applyTaggingAgent_smart.py                            │
│  └─ ai_apply_from_json_smart()                                  │
│                                                                  │
│  For each file in apply_plan_smart.json:                        │
│                                                                  │
│  Step 1: Idempotency Check                                      │
│  └─ Quick filter: Is tracking function name already present?    │
│  └─ If yes → LLM deep check (uses Vegas LLM)                    │
│     • Pass Tagging framework code to LLM                        │
│     • Pass target file content to LLM                           │
│     • Ask: "Is tracking already properly implemented?"          │
│     • If already tagged → SKIP (prevent duplicates)             │
│                                                                  │
│  Step 2: Intelligent Prompt Building                            │
│  └─ SmartPromptBuilder.build_intelligent_prompt()               │
│  └─ Creates context-aware prompt with:                          │
│     • ACTUAL Tagging framework source code                      │
│     • Target file content                                       │
│     • Instruction: What function, params, where                 │
│     • Framework becomes LLM's "source of truth"                 │
│                                                                  │
│  Step 3: LLM Code Generation                                    │
│  └─ VegasLLMWrapper.invoke(prompt)                              │
│  └─ LLM analyzes:                                               │
│     • What imports are needed from framework                    │
│     • What hooks to call (useTagging)                           │
│     • Where to place tracking calls                             │
│     • What parameters to pass (from spec)                       │
│  └─ LLM returns ONLY when:                                      │
│     ✓ Already tagged → "unchanged" with reason                  │
│     ✓ Code added → updated file content as JSON                 │
│                                                                  │
│  Step 4: Change Tracking & Write                                │
│  └─ Compare original vs updated file                            │
│  └─ If no changes needed → Mark as processed                    │
│  └─ If changes needed:                                          │
│     • Create .taggingai.bak backup                              │
│     • Write updated file                                        │
│     • Log what was added (imports, hooks, calls)                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ STAGE 5: REPORTING & LOGGING                                     │
│ ──────────────────────────────────────────────────────────────── │
│                                                                  │
│  Output Files:                                                  │
│  ├─ apply_log_smart.json                                        │
│  │  └─ Per-file results, success/failure reasons                │
│  │  └─ What was added to each file (imports, hooks, calls)      │
│  │                                                              │
│  └─ Backups with .taggingai.bak extension                       │
│     └─ Original file before changes                             │
│                                                                  │
│  Summary Statistics:                                            │
│  └─ Success count, Failed count, Skipped count                  │
│  └─ Aggregate imports added, hooks added, calls added           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Key Design Patterns

### 1. **No Hardcoding - Framework-Driven**
- The system reads the ACTUAL Tagging framework code
- Passes it directly to the LLM as context
- LLM learns what functions exist, what parameters they need
- No hardcoded import paths, function names, or parameters
- When framework changes → System automatically adapts

### 2. **Idempotency - Smart Deduplication**
- Pre-check: Function name present in file?
- Deep check: Is tracking already properly implemented?
- Uses LLM to intelligently detect existing tagging
- Prevents duplicate tracking calls
- Safe to run multiple times

### 3. **Three Data Format Support**
The system supports three JSON input formats:

**Format 1: Direct Array (Preferred)**
```json
[
  {
    "file": "src/pages/.../index.js",
    "description": "...",
    "eventType": "page_load",
    "suggestedFunction": "trackPageLoad",
    "suggestedParameters": {...}
  }
]
```

**Format 2: Items Wrapper**
```json
{
  "items": [
    {
      "file": "...",
      ...
    }
  ]
}
```

**Format 3: Hierarchical (Legacy)**
```json
{
  "src/pages/.../index.js:21": {
    "description": "...",
    ...
  }
}
```

### 4. **LLM Context Window Optimization**
- Smart Prompt Builder includes:
  - Actual framework source code
  - Target file content
  - Clear task requirements
  - Parameter mapping
  - Key rules and constraints
- Prompt is structured to help LLM understand:
  - What's available (framework)
  - What needs changing (target file)
  - What exactly to do (instruction)

---

## File Dependencies & Workflow

### Core Entry Points

**1. taggingSuggestion.py** - Initial Analysis
```python
main()
  └─ Clones repository from REPO_URL
  └─ Calls analyze_tagging_requirements()
  └─ Generates: tagging_report.json
```

**2. applyTagging_smart.py** - Conversion & Orchestration
```python
main()
  └─ Loads tagging_report.json
  └─ Calls convert_report_to_apply_format()
  └─ Generates: apply_plan_smart.json
  └─ Calls ai_apply_from_json_smart()
  └─ Reports: apply_log_smart.json
```

**3. applyTaggingAgent_smart.py** - LLM Application
```python
ai_apply_from_json_smart()
  └─ For each file:
     ├─ check_tagging_with_llm()         # Idempotency check
     ├─ _ai_edit_file_smart()            # LLM code generation
     └─ Write results to file            # File updates
```

### Key Module Dependencies

```
applyTagging_smart.py
├─ applyTaggingAgent_smart.py
│  ├─ tools.vegas_llm_utils.VegasLLMWrapper
│  │  └─ Uses Vegas LLM API
│  │
│  └─ tools.smart_prompt_builder.SmartPromptBuilder
│     ├─ Reads Tagging framework
│     ├─ Analyzes target files
│     └─ Builds intelligent prompts
│
└─ tools.taggingApplier (legacy, not used in smart version)
```

---

## Data Flow

### Input: actionable_item.json
```json
[
  {
    "file": "src/pages/ExpressStore/PayBill/PayBillType/index.js",
    "description": "Bill type selection page load",
    "eventType": "page_load",
    "suggestedFunction": "trackPageLoad",
    "context": "useEffect hook on component mount",
    "suggestedParameters": {
      "pageName": "Bill type AI",
      "flow": "BPK Bill type",
      "subFlow": "Bill Type Options",
      "event": "BillType_Page_Load"
    }
  }
]
```

### Processing Steps

1. **Load** → taggingSuggestion.py reads actionable_item.json
2. **Clone** → Fetch repo from REPO_URL
3. **Analyze** → Find files, verify they exist
4. **Report** → Create tagging_report.json with metadata
5. **Convert** → Transform to apply_plan_smart.json format
6. **Check** → Idempotency: Already tagged? Skip or LLM verify
7. **Generate** → LLM creates code with imports + hooks + calls
8. **Update** → Write changes, create backups
9. **Log** → Document success/failure for each file

---

## Vegas LLM Integration

### Why Vegas LLM?
- **Code Understanding**: Reads actual framework code
- **Context Awareness**: Understands target file structure
- **Intelligent Decisions**: Figures out imports, placement, parameters
- **Framework-Aware**: No assumptions, uses real code as source of truth

### Prompt Structure
```
[TAGGING FRAMEWORK SOURCE CODE]
    ↓
[LLM reads actual functions, parameters, usage patterns]
    ↓
[TARGET FILE CONTENT]
    ↓
[LLM understands existing code structure]
    ↓
[TASK REQUIREMENTS]
    ↓
[LLM generates correct imports, hooks, and calls]
    ↓
[UPDATED FILE CONTENT + METADATA]
```

### LLM Responsibilities (NOT Hardcoded)
✅ Detect what imports are needed
✅ Calculate correct relative import paths
✅ Understand how to call useTagging hook
✅ Determine best placement for tracking calls
✅ Match required parameters exactly
✅ Preserve all other code unchanged
✅ Detect if already tagged (idempotency)

---

## Configuration (.env)

```bash
# LLM Integration
VEGAS_API_KEY=your_key_here
context_name=context_value
usecase_name=usecase_value

# Repository
REPO_URL=https://github.com/your/repo.git
REPO_BRANCH=main
CLONE_LOCAL=cloned_repo

# Specification File
JSON_SPEC_FILE=./actionable_item.json
```

---

## Output Files

### 1. **tagging_report.json** - Analysis Results
- Generated by: taggingSuggestion.py
- Contains: List of files found + metadata
- Usage: Input to applyTagging_smart.py

### 2. **apply_plan_smart.json** - Conversion Plan
- Generated by: applyTagging_smart.py → convert_report_to_apply_format()
- Contains: Flat array of items with file + instruction details
- Usage: Input to applyTaggingAgent_smart.py

### 3. **apply_log_smart.json** - Application Results
- Generated by: applyTaggingAgent_smart.py → ai_apply_from_json_smart()
- Contains: Per-file results, what was added, success/failure reasons
- Usage: Review and audit trail

### 4. **Backup Files** (.taggingai.bak)
- Created before writing updates
- Allows rollback if needed
- Safe to delete after verification

---

## Error Handling

### File Not Found
- Checks if file exists in repository
- Skips with warning in logs
- Counted as failed item

### LLM Errors
- If Vegas LLM fails: Falls back to no changes
- Logs reason in apply_log_smart.json
- Counted as failed item

### JSON Parsing Errors
- If LLM response can't be parsed
- Falls back to no changes
- Logs "Could not extract JSON from LLM response"

### Backup Failures
- If can't create backup: Skips write (safety measure)
- Logs reason
- Original file untouched

---

## Performance & Optimization

### Idempotency Check Two-Tier
```
Tier 1: Quick String Filter (Fast)
└─ Is function name present in file?

Tier 2: LLM Deep Check (Smart)
└─ Only if Tier 1 matches
└─ LLM verifies proper implementation
└─ Prevents false positives
```

### Caching & Reuse
- Framework code read once (not per-file)
- Prompt builder initialized once
- Vegas LLM instance reused

---

## Security & Safeguards

1. **Backups Created** - Before any write operations
2. **Dry-Run Mode** - Can test without writing
3. **Idempotent** - Safe to run multiple times
4. **Read-Only Verification** - Checks file exists before reading
5. **No Eval/Exec** - All LLM output validated as JSON

---

## Summary

This is a **sophisticated, framework-aware tagging system** that:
- ✅ Reads actual framework code (not hardcoded)
- ✅ Uses LLM to intelligently understand context
- ✅ Prevents duplicate tagging (idempotency)
- ✅ Supports multiple input formats
- ✅ Creates safe backups
- ✅ Provides detailed logging
- ✅ Requires no manual code editing

The key innovation is passing the ACTUAL tagging framework source code to the LLM, letting it make intelligent decisions rather than relying on hardcoded patterns.
