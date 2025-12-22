# Unified Entry Point - Complete Workflow

## 🎯 One Command, Two Phases

Now you have a **single, unified entry point** that does everything:

```bash
python core/applyTagging_smart.py
```

This command automatically runs **BOTH**:
1. **Phase 1**: Apply tracking code (trackPageLoad, etc.)
2. **Phase 2**: Apply data-track attributes to interactive elements

---

## Complete Workflow

```
Step 1: Generate Report (ONE TIME ONLY)
┌──────────────────────────────────────┐
│ python core/taggingSuggestion.py     │
│ └─ Creates: tagging_report.json      │
└──────────────────────────────────────┘
           ↓
Step 2: Apply Everything (UNIFIED)
┌──────────────────────────────────────────────────────┐
│ python core/applyTagging_smart.py                    │
│                                                      │
│ Phase 1: Tracking Code                              │
│ ├─ Imports tracking functions                       │
│ ├─ Adds useTagging() hook                           │
│ └─ Calls trackPageLoad() with parameters            │
│                                                      │
│ Phase 2: Data-Track Attributes                      │
│ ├─ Identifies buttons and onClick elements          │
│ ├─ Generates semantic values (LLM)                  │
│ └─ Adds data-track="value" attributes               │
│                                                      │
│ Outputs:                                             │
│ ├─ apply_log_smart.json (tracking results)          │
│ ├─ data_track_report.json (data-track results)      │
│ └─ Modified source files with BOTH changes          │
└──────────────────────────────────────────────────────┘
           ↓
Result: Files with BOTH ✓
├─ Tracking code (trackPageLoad)
└─ Data-track attributes (data-track="value")
```

---

## What Happens When You Run It

### Command
```bash
python core/applyTagging_smart.py
```

### Output (Detailed Progress)

```
======================================================================
 Smart Agentic Tagging System - LLM-Aware Framework
======================================================================
• JSON Spec      : actionable_item.json
• Repo Path      : cloned_repo
• Vegas LLM      : Available

📖 Loading report: core/outputs/tagging_report.json
🔄 Converting to smart apply format...
✓ Apply plan saved: core/outputs/apply_plan_smart.json
📊 Items to process: 3

======================================================================
 Applying Tags with SMART Vegas LLM (Framework-Aware)
======================================================================
✓ Successfully applied    : 3
✗ Failed                 : 0
⊘ Skipped (already tagged): 0

📊 Tracking Statistics:
   • Imports added   : 3
   • Hooks added     : 3
   • Calls added     : 3

✓ All files tagged successfully!
  Backups saved with .taggingai.bak extension

======================================================================
 PHASE 2: Applying Data-Track Attributes
======================================================================
🚀 Starting data-track attribute application...

[3/3] 📄 PayBillType/index.js
  🔍 Extracting interactive elements...
  ✓ Found 5 interactive elements
  🎯 Generating data-track values...
    ✓ Element 1: data-track="pay-bill"
    ✓ Element 2: data-track="cancel"
    ✓ Element 3: data-track="close-modal"
  ✏️  Applying 3 data-track attributes...
  ✓ File updated successfully

======================================================================
Data-Track Application Summary
======================================================================
✓ Files processed        : 3
✓ Successfully modified  : 3
✗ Failed                 : 0
📊 Elements processed    : 15
📊 Data-track added      : 12
⊘ Elements skipped       : 3

✓ Data-track attributes applied successfully!
  Backups saved with .datatrack.bak extension

======================================================================
UNIFIED PIPELINE COMPLETE ✓
======================================================================

✅ Phase 1: Tracking Code Applied
   └─ Files: 3 success, 0 failed

✅ Phase 2: Data-Track Attributes Applied
   └─ Files: 3 success, 0 failed
   └─ Elements: 12 modified

📂 All outputs saved in: core/outputs
✓ Complete!
```

---

## Before vs After

### Before Running Script
```javascript
// PayBill/index.js
function PayBillPage() {
  return (
    <div>
      <button onClick={handlePayment}>
        Pay Bill
      </button>
      <button onClick={handleCancel}>
        Cancel
      </button>
    </div>
  );
}
```

### After Running Script
```javascript
// PayBill/index.js
import { useTagging } from '../../Tagging';  // ← Added by Phase 1

function PayBillPage() {
  const { trackPageLoad } = useTagging();     // ← Added by Phase 1
  
  useEffect(() => {                           // ← Added by Phase 1
    trackPageLoad({
      pageName: "Bill payment",
      flow: "BPK Bill payment"
    });
  }, []);                                     // ← Added by Phase 1

  return (
    <div>
      <button data-track="pay-bill"           // ← Added by Phase 2
              onClick={handlePayment}>
        Pay Bill
      </button>
      <button data-track="cancel"             // ← Added by Phase 2
              onClick={handleCancel}>
        Cancel
      </button>
    </div>
  );
}
```

---

## Files Generated

### Phase 1 Outputs
- **apply_log_smart.json** - Tracking code application results
- **apply_plan_smart.json** - Converted from tagging_report.json
- **Files backup** - .taggingai.bak (original before tracking code)
- **Modified files** - With tracking imports, hooks, and calls

### Phase 2 Outputs
- **data_track_report.json** - Data-track application results
- **Files backup** - .datatrack.bak (original before data-track)
- **Modified files** - With data-track attributes

### Combined Results
All files have **BOTH**:
1. Tracking code
2. Data-track attributes

---

## Flow Diagram

```
START: User runs script
│
├─ applyTagging_smart.py main()
│  │
│  ├─ PHASE 1: Apply Tracking Code
│  │  │
│  │  ├─ Load tagging_report.json
│  │  ├─ Convert to apply_plan.json
│  │  ├─ Call ai_apply_from_json_smart()
│  │  │  └─ Apply imports, hooks, calls
│  │  ├─ Print Phase 1 Summary
│  │  └─ Log results to apply_log_smart.json
│  │
│  ├─ PHASE 2: Apply Data-Track (NEW)
│  │  │
│  │  ├─ Call apply_data_track_attributes_smart()
│  │  │  │
│  │  │  ├─ Load tagging_report.json (same file)
│  │  │  ├─ For each file:
│  │  │  │  ├─ Extract interactive elements
│  │  │  │  ├─ Generate data-track values (LLM)
│  │  │  │  ├─ Apply attributes
│  │  │  │  └─ Create backup
│  │  │  └─ Return statistics
│  │  │
│  │  ├─ Print Phase 2 Summary
│  │  └─ Log results to data_track_report.json
│  │
│  └─ Print Unified Summary
│     └─ Both phases together
│
└─ END: All complete!
```

---

## Configuration

### .env File
```bash
# Required for both phases
VEGAS_API_KEY=your_key
context_name=context
usecase_name=usecase
REPO_URL=https://github.com/your/repo.git
CLONE_LOCAL=cloned_repo
JSON_SPEC_FILE=./actionable_item.json
```

---

## Error Handling

If any errors occur in Phase 1:
- Phase 2 still runs (if available)
- Both phases logged independently
- No data loss - backups created before each phase

If any errors occur in Phase 2:
- Phase 1 results are preserved
- Error logged in data_track_report.json
- Backups prevent data loss

---

## Outputs Location

```
core/outputs/
├─ tagging_report.json              (from taggingSuggestion.py)
├─ apply_plan_smart.json            (Phase 1: converted plan)
├─ apply_log_smart.json             (Phase 1: results)
└─ data_track_report.json           (Phase 2: results)

cloned_repo/
├─ src/pages/.../index.js           (modified file)
├─ src/pages/.../index.js.taggingai.bak (backup from Phase 1)
└─ src/pages/.../index.js.datatrack.bak (backup from Phase 2)
```

---

## Summary

### Before This Update
You needed **2 separate commands**:
```bash
python core/taggingSuggestion.py
python core/applyTagging_smart.py        # Phase 1
python core/applyDataTrack_smart.py      # Phase 2
```

### After This Update
You need **1 unified command**:
```bash
python core/taggingSuggestion.py
python core/applyTagging_smart.py        # Does BOTH phases!
```

---

## How to Use

### Complete Workflow
```bash
# Step 1: Analyze files (one time)
python core/taggingSuggestion.py

# Step 2: Apply EVERYTHING (tracking + data-track)
python core/applyTagging_smart.py

# Step 3: Check results
cat core/outputs/apply_log_smart.json
cat core/outputs/data_track_report.json
```

### If Only Phase 2 Fails
- Phase 1 tracking code is already applied
- Check `data_track_report.json` for issues
- You can still use the files (they have tracking code)

### If Only Phase 1 Fails
- Phase 2 won't run (no tracking code to complement)
- Review `apply_log_smart.json` for tracking issues
- Fix issues and re-run

---

## Next Steps

1. ✅ Make sure .env is configured
2. ✅ Run `python core/taggingSuggestion.py`
3. ✅ Run `python core/applyTagging_smart.py` (ONE COMMAND for both phases)
4. ✅ Check outputs in `core/outputs/`

---

**Status**: ✅ Unified entry point ready to use!
