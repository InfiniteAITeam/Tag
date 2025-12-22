# Data-Track System - Visual Quick Reference

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SMART TAGGING ECOSYSTEM                          │
│                    (Tracking + Data-Track)                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ INPUT LAYER                                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  actionable_item.json                                              │
│  ├─ file: "src/pages/PayBill/index.js"                             │
│  ├─ description: "Bill payment page"                               │
│  ├─ eventType: "page_load"                                         │
│  └─ suggestedFunction: "trackPageLoad"                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ANALYSIS LAYER (taggingSuggestion.py)                              │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Clone repository from REPO_URL                                  │
│ 2. Locate files mentioned in actionable_item.json                  │
│ 3. Verify files exist and are readable                             │
│ 4. Generate tagging_report.json with metadata                      │
│                                                                     │
│ OUTPUT: tagging_report.json                                        │
│ ├─ files: [                                                        │
│ │   {                                                              │
│ │     "file": "src/pages/PayBill/index.js",                        │
│ │     "description": {...},                                        │
│ │     "taggingInstructions": {...}                                 │
│ │   }                                                              │
│ │ ]                                                                │
│ └─ tagging_framework: "src/pages/ExpressStore/Tagging/"            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                                           ↓
┌──────────────────────────┐          ┌────────────────────────────┐
│ TRACKING CODE PATH       │          │ DATA-TRACK PATH (NEW)      │
│ (applyTagging_smart.py)  │          │ (applyDataTrack_smart.py)  │
├──────────────────────────┤          ├────────────────────────────┤
│                          │          │                            │
│ 1. Convert to apply plan │          │ 1. Extract interactive      │
│ 2. Check idempotency     │          │    elements (buttons, etc)  │
│ 3. Generate with LLM:    │          │ 2. Generate values (LLM):   │
│    ├─ imports            │          │    "Pay Bill" → "pay-bill"  │
│    ├─ hooks              │          │ 3. Apply attributes (LLM)   │
│    └─ calls              │          │ 4. Create backups           │
│ 4. Apply changes         │          │ 5. Write updated files      │
│ 5. Create backups        │          │ 6. Generate reports         │
│ 6. Log results           │          │                            │
│                          │          │                            │
│ OUTPUT:                  │          │ OUTPUT:                    │
│ ├─ Modified files with   │          │ ├─ Modified files with     │
│ │  tracking code         │          │ │  data-track attributes   │
│ ├─ Backup (.bak)         │          │ ├─ Backup (.datatrack.bak) │
│ └─ apply_log_smart.json  │          │ └─ data_track_report.json  │
│                          │          │                            │
└──────────────────────────┘          └────────────────────────────┘
        │                                     │
        └─────────────────────┬───────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ OUTPUT LAYER - Modified Source Files                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Example: PayBill/index.js (with both tracking + data-track)       │
│                                                                     │
│  import { useTagging } from '../../Tagging';                       │
│                                                                     │
│  function PayBillPage() {                                          │
│    const { trackPageLoad } = useTagging();                         │
│                                                                     │
│    useEffect(() => {                                               │
│      trackPageLoad({                                               │
│        pageName: "Bill payment",                                   │
│        flow: "BPK Bill payment"                                    │
│      });                                                           │
│    }, []);                                                         │
│                                                                     │
│    return (                                                        │
│      <button data-track="pay-bill" onClick={handlePay}>           │
│        Pay Bill                                                    │
│      </button>                                                     │
│    );                                                              │
│  }                                                                 │
│                                                                     │
│  └─ Has BOTH:                                                      │
│     ├─ trackPageLoad (tracking code)                               │
│     └─ data-track="pay-bill" (element attribute)                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
START
  ↓
  │ actionable_item.json
  ├─ File paths
  ├─ Event types
  └─ Parameters
  ↓
taggingSuggestion.py
  ├─ Clone repo
  ├─ Locate files
  └─ Generate report
  ↓
tagging_report.json ─────────────────┐
  │ Files to process                 │
  │ Metadata                         │
  │ Instructions                     │
  │                                  │
  ├─ Path A: Tracking Code           │ ├─ Path B: Data-Track (NEW)
  │                                  │ │
  ↓                                  ↓ ↓
applyTagging_smart.py          applyDataTrack_smart.py
  ├─ LLM generates                  ├─ Extract elements
  │  ├─ imports                     ├─ Generate values
  │  ├─ hooks                       ├─ Apply attributes
  │  └─ calls                       └─ Log results
  │                                  ↓
  ↓                              data_track_report.json
apply_log_smart.json
  
RESULT: Files with BOTH ✓
├─ Tracking code (trackPageLoad)
└─ Data-track attributes
```

---

## Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│ applyDataTrack_smart.py (Main Orchestrator)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ Load tagging_report.json                                   │
│  │                                                              │
│  └─→ For each file:                                             │
│      │                                                          │
│      ├─ ElementExtractor                                        │
│      │  │                                                       │
│      │  ├─ Find <button> elements                               │
│      │  ├─ Find <div onClick> elements                          │
│      │  ├─ Find <span onClick> elements                         │
│      │  └─ Extract attributes, text, line numbers              │
│      │      ↓                                                   │
│      │      List of InteractiveElement objects                  │
│      │                                                          │
│      ├─ For each element:                                       │
│      │  │                                                       │
│      │  ├─ Check: already has data-track?                       │
│      │  │  └─ YES: skip (idempotency)                           │
│      │  │  └─ NO: continue                                      │
│      │  │                                                       │
│      │  ├─ ValueSanitizer                                       │
│      │  │  └─ Extract meaningful text                           │
│      │  │      (inner_text, title, aria-label, etc.)           │
│      │  │      ↓                                                │
│      │  │      "Pay Bill" (raw text)                            │
│      │  │                                                       │
│      │  └─ DataTrackApplier                                     │
│      │     │                                                    │
│      │     ├─ generate_value_with_llm()                        │
│      │     │  │ Prompt: "Generate semantic data-track value"   │
│      │     │  │ LLM: "pay-bill"                                │
│      │     │  ↓                                                 │
│      │     │  ValueSanitizer.sanitize()                        │
│      │     │  └─ Validate & format: "pay-bill"                 │
│      │     │                                                    │
│      │     └─ apply_data_track_with_llm()                      │
│      │        │ Prompt: "Add data-track to code"               │
│      │        │ LLM: "Updated file with attributes"            │
│      │        ↓                                                 │
│      │        Updated file content                              │
│      │                                                          │
│      ├─ Create backup (.datatrack.bak)                          │
│      ├─ Write updated file                                      │
│      └─ Log results                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Execution Timeline

```
Time          Activity                    Component
────          ────────────────────────   ──────────────────────
T+0s          Start                       applyDataTrack_smart.py
T+1s          Load tagging_report.json    
T+2s          Read first file             File I/O
T+3s          Extract elements            ElementExtractor
              (regex parsing)
T+4s          Generate value (LLM call)   VegasLLMWrapper
              "Pay Bill" → "pay-bill"     (2-10 seconds)
T+14s         Generate more values        DataTrackApplier
T+24s         Apply attributes (LLM)      LLM code generation
              (2-5 seconds per file)
T+29s         Create backup               File I/O
T+30s         Write updated file          File I/O
T+31s         Log results                 JSON report
T+32s         Generate report             data_track_report.json
T+33s         Complete                    ✓
```

---

## Class Hierarchy

```
ElementExtractor
├─ _find_button_elements()
├─ _find_onclick_elements()
├─ _find_routing_components()
├─ _parse_attributes()
└─ extract_all_interactive_elements() → List[InteractiveElement]

InteractiveElement
├─ element_type: ElementType
├─ line_number: int
├─ inner_text: str
├─ attributes: Dict[str, str]
├─ has_data_track: bool
└─ to_dict() → Dict

ElementType (Enum)
├─ BUTTON = "button"
├─ DIV = "div"
├─ SPAN = "span"
├─ INPUT = "input"
├─ LINK = "link"
└─ ANCHOR = "anchor"

ValueSanitizer
├─ sanitize(raw_value) → str
├─ is_valid_value(value) → bool
└─ extract_text_from_element(element) → str

DataTrackPromptBuilder (Static Methods)
├─ build_element_detection_prompt()
├─ build_value_generation_prompt()
├─ build_code_generation_prompt()
└─ build_check_already_exists_prompt()

DataTrackApplier
├─ extract_json_from_response()
├─ detect_elements_with_llm()
├─ generate_value_with_llm()
└─ apply_data_track_with_llm()

VegasLLMWrapper (Existing)
└─ invoke(prompt) → str
```

---

## Value Generation Example

```
INPUT ELEMENT:
<button onClick={handlePayment} className="pay-btn">
  Pay Bill
</button>

PROCESS:
┌──────────────────────────────────────────┐
│ ElementExtractor                         │
├──────────────────────────────────────────┤
│ Find: <button ...>...</button>           │
│ Extract:                                 │
│  - element_type: "button"                │
│  - inner_text: "Pay Bill"                │
│  - line_number: 42                       │
│  - attributes: {                         │
│      "onClick": "handlePayment",         │
│      "className": "pay-btn"              │
│    }                                     │
│  - has_data_track: false                 │
└──────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────┐
│ ValueSanitizer                           │
├──────────────────────────────────────────┤
│ Extract text: "Pay Bill"                 │
│ Sanitize:                                │
│  1. Lowercase: "pay bill"                │
│  2. Replace spaces: "pay-bill"           │
│  3. Remove special chars: "pay-bill"     │
│  4. Validate: ✓ valid                    │
│                                          │
│ Result: "pay-bill"                       │
└──────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────┐
│ DataTrackApplier (LLM)                   │
├──────────────────────────────────────────┤
│ Prompt: Generate semantic value          │
│ Element: <button>Pay Bill</button>       │
│ Text: "Pay Bill"                         │
│                                          │
│ LLM Response:                            │
│ {                                        │
│   "data_track_value": "pay-bill",        │
│   "reasoning": "User pays bill",         │
│   "confidence": "high"                   │
│ }                                        │
│                                          │
│ Validate: ✓ valid                        │
└──────────────────────────────────────────┘
              ↓
OUTPUT VALUE:
"pay-bill" (high confidence)

FINAL ELEMENT:
<button data-track="pay-bill" onClick={handlePayment} className="pay-btn">
  Pay Bill
</button>
```

---

## Decision Tree: Should Element Get data-track?

```
START: Element found
│
├─ Already has data-track="..."?
│  ├─ YES → skip_if_already=true?
│  │        ├─ YES → SKIP (idempotency)
│  │        └─ NO → Process anyway
│  │
│  └─ NO → Continue
│
├─ Is interactive? (button, onClick, etc.)
│  ├─ NO → SKIP (not interactive)
│  └─ YES → Continue
│
├─ Can extract meaningful text?
│  ├─ NO → SKIP (can't determine what element does)
│  └─ YES → Continue
│
├─ Generate data-track value
│  ├─ LLM available → Generate with LLM
│  └─ LLM unavailable → Sanitize extracted text
│
├─ Is generated value valid?
│  ├─ NO → SKIP (value not meaningful)
│  └─ YES → Continue
│
├─ Can apply change to file?
│  ├─ NO → SKIP (error applying)
│  └─ YES → Continue
│
├─ Create backup?
│  ├─ NO → ABORT (safety measure)
│  └─ YES → Continue
│
├─ Write file?
│  ├─ NO → SKIP (write error)
│  └─ YES → Continue
│
└─ LOG SUCCESS ✓
```

---

## Error Handling Flow

```
ERROR DETECTED
│
├─ File Not Found
│  └─ LOG: "File not found: path"
│     SKIP: File
│     COUNT: fail += 1
│
├─ File Read Error
│  └─ LOG: "Could not read: reason"
│     SKIP: File
│     COUNT: fail += 1
│
├─ Element Extraction Error
│  └─ LOG: "Could not extract elements"
│     ACTION: Continue with zero elements
│     COUNT: File marked "no_elements"
│
├─ LLM Error
│  └─ LOG: "LLM failed: error"
│     ACTION: Use fallback (sanitize text)
│     RESULT: Lower confidence score
│
├─ Invalid Generated Value
│  └─ LOG: "Invalid value: value"
│     ACTION: Try fallback
│     RESULT: Skip element or use default
│
├─ Backup Creation Failed
│  └─ LOG: "Backup failed: reason"
│     ACTION: ABORT (don't modify file)
│     COUNT: fail += 1
│
├─ File Write Failed
│  └─ LOG: "Write failed: reason"
│     ACTION: Restore from attempt
│     COUNT: fail += 1
│
└─ All errors logged in data_track_report.json
```

---

## Integration Points

```
EXISTING SYSTEM          NEW SYSTEM
───────────────         ──────────
taggingSuggestion.py
       ↓
tagging_report.json ←─── Shared Input
       ↓
applyTagging_smart.py
       ↓
Updated files with       applyDataTrack_smart.py ←── Uses same report
tracking code            
       ↓                        ↓
apply_log_smart.json    data_track_report.json
       
RESULT:
Files with BOTH
├─ trackPageLoad() calls
└─ data-track="value" attributes
```

---

## File Before & After Comparison

```
BEFORE:
┌────────────────────────────────────────┐
│ src/pages/PayBill/index.js             │
├────────────────────────────────────────┤
│ function PayBillPage() {               │
│   return (                             │
│     <div>                              │
│       <button onClick={pay}>           │
│         Pay Bill                       │
│       </button>                        │
│       <button onClick={cancel}>        │
│         Cancel                         │
│       </button>                        │
│     </div>                             │
│   );                                   │
│ }                                      │
└────────────────────────────────────────┘

AFTER (with applyDataTrack_smart.py):
┌────────────────────────────────────────┐
│ src/pages/PayBill/index.js             │
├────────────────────────────────────────┤
│ function PayBillPage() {               │
│   return (                             │
│     <div>                              │
│       <button data-track="pay-bill"    │
│               onClick={pay}>           │
│         Pay Bill                       │
│       </button>                        │
│       <button data-track="cancel"      │
│               onClick={cancel}>        │
│         Cancel                         │
│       </button>                        │
│     </div>                             │
│   );                                   │
│ }                                      │
└────────────────────────────────────────┘

AFTER (with BOTH tracking + data-track):
┌────────────────────────────────────────┐
│ src/pages/PayBill/index.js             │
├────────────────────────────────────────┤
│ import { useTagging } from '...';      │ ← Added by applyTagging_smart.py
│                                        │
│ function PayBillPage() {               │
│   const { trackPageLoad } = (...);     │ ← Added by applyTagging_smart.py
│                                        │
│   useEffect(() => {                    │ ← Added by applyTagging_smart.py
│     trackPageLoad({...});              │ ← Added by applyTagging_smart.py
│   }, []);                              │ ← Added by applyTagging_smart.py
│                                        │
│   return (                             │
│     <div>                              │
│       <button data-track="pay-bill"    │ ← Added by applyDataTrack_smart.py
│               onClick={pay}>           │
│         Pay Bill                       │
│       </button>                        │
│       <button data-track="cancel"      │ ← Added by applyDataTrack_smart.py
│               onClick={cancel}>        │
│         Cancel                         │
│       </button>                        │
│     </div>                             │
│   );                                   │
│ }                                      │
└────────────────────────────────────────┘
```

---

## Report Statistics

```
┌────────────────────────────────────────────────────┐
│ data_track_report.json Summary                     │
├────────────────────────────────────────────────────┤
│                                                    │
│  Stats:                                            │
│  ├─ total_files: 3                                 │
│  ├─ processed: 3                                   │
│  ├─ success: 3                                     │
│  ├─ failed: 0                                      │
│  ├─ total_elements_found: 15                       │
│  ├─ total_elements_modified: 12                    │
│  ├─ total_elements_skipped: 3                      │
│  │  └─ (already had data-track)                    │
│  └─ backup_created: 3                              │
│                                                    │
│  Per-File Results:                                 │
│  ├─ File 1: ✓ Success (4 elements modified)       │
│  ├─ File 2: ✓ Success (5 elements modified)       │
│  └─ File 3: ✓ Success (3 elements modified)       │
│                                                    │
│  Element Confidence:                               │
│  ├─ High: 12 (LLM highly confident)               │
│  ├─ Medium: 3 (fallback or complex)               │
│  └─ Low: 0 (errors or missing context)            │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## Command Reference

```bash
# 1. Generate tagging report (must do first)
python core/taggingSuggestion.py

# 2. Apply data-track attributes (main command)
python core/applyDataTrack_smart.py

# 3. Check results
cat core/outputs/data_track_report.json

# 4. Verify backups were created
find cloned_repo/ -name "*.datatrack.bak" | head -5

# 5. View diff (if using git)
git diff cloned_repo/

# 6. Restore from backup if needed
cp cloned_repo/src/pages/PayBill/index.js.datatrack.bak \
   cloned_repo/src/pages/PayBill/index.js
```

---

## Key Takeaways

✅ **Automatic**: No manual coding required
✅ **Smart**: Uses LLM for intelligent decisions
✅ **Safe**: Backups before any modification
✅ **Idempotent**: Safe to run multiple times
✅ **Integrated**: Uses same input as tracking system
✅ **Comprehensive**: Detailed reporting and logging
✅ **Flexible**: Works standalone or with tracking code
✅ **Adaptive**: No hardcoding - works with any codebase
