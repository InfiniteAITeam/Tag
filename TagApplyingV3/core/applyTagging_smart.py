#!/usr/bin/env python
"""
Smart Apply Tagging - Unified Tagging Pipeline

This script orchestrates a complete two-phase tagging system:

PHASE 1: Tracking Code Application
1. Reads tagging_report.json (from taggingSuggestion.py)
2. Converts it to apply_plan.json format
3. Calls smart agent which:
   - Reads the ACTUAL Tagging framework
   - Passes it to LLM for intelligent decisions
   - Lets LLM figure out imports, hooks, and calls (no hardcoding)

PHASE 2: Data-Track Attribute Application (NEW)
1. Uses same tagging_report.json
2. Identifies interactive elements (buttons, onClick divs, etc.)
3. Generates semantic data-track values using LLM
4. Applies data-track attributes to elements

ONE ENTRY POINT - Both phases run automatically with single command:
    python core/applyTagging_smart.py
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

from applyTaggingAgent_smart import ai_apply_from_json_smart

# Import data-track functionality
try:
    from applyDataTrack_smart import apply_data_track_attributes_smart
    DATA_TRACK_AVAILABLE = True
except ImportError:
    DATA_TRACK_AVAILABLE = False
    print("⚠️  Data-track module not available (optional)")

CORE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = CORE_DIR / "outputs"
PROJECT_ROOT = CORE_DIR.parent


def convert_report_to_apply_format(tagging_report: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
    """
    Convert tagging_report.json format to applyTaggingAgent_smart.py input format.
    
    The smart agent expects files to have:
    {
        "file": "path/to/file.js",
        "file_path": "src/path/to/file.js",
        "action": "page_load|click|error",
        "event": "trackPageLoad|trackPageChange|trackPageNotification",
        "description": "What to tag",
        "suggested_params": {...},
        "top_match": {"line": N}
    }
    """
    items = []
    repo_path_obj = Path(repo_path)
    
    for file_info in tagging_report.get("files", []):
        file_path = file_info.get("file", "")
        if not file_path:
            continue
            
        # Check if file exists
        full_path = repo_path_obj / file_path
        if not full_path.exists():
            print(f"⚠️  Skipping missing file: {file_path}")
            continue
        
        description = file_info.get("description", {})
        tagging_instructions = file_info.get("taggingInstructions", {})
        
        # Handle both old format (string) and new format (dict)
        if isinstance(description, dict):
            # New format: description is a dict with eventType, suggestedFunction, etc.
            description_text = description.get("description", "")
            event_type = description.get("eventType", "page_load")
            action = event_type
            event_name = description.get("suggestedFunction", "trackPageLoad")
        else:
            # Old format: description is a string
            description_text = description
            action = "page_load"
            event_name = "trackPageLoad"
            if "click" in description_text.lower() or "select" in description_text.lower():
                action = "click"
                event_name = "trackPageChange"
            elif "error" in description_text.lower() or "notification" in description_text.lower():
                action = "error"
                event_name = "trackPageNotification"
        
        item = {
            "file": str(repo_path_obj / file_path),  # Absolute path to file
            "file_path": file_path,
            "action": action,
            "event": event_name,
            "description": description_text,
            "suggested_event_name": event_name,
            "suggested_params": (
                description.get("suggestedParameters", {})
                if isinstance(description, dict)
                else tagging_instructions.get("parameters", {})
            ),
            "top_match": {
                "line": tagging_instructions.get("lineNumber", 1)
            }
        }
        
        items.append(item)
    
    return {
        "items": items,
        "spec_version": "2.1",
        "description": "Auto-generated from tagging_report.json - Smart LLM-Aware Format"
    }


def main():
    load_dotenv()
    
    # Check Vegas LLM is available
    vegas_api_key = os.getenv("VEGAS_API_KEY")
    if not vegas_api_key:
        print("✗ VEGAS_API_KEY not set in .env")
        print("  The tagging application requires Vegas LLM integration.")
        sys.exit(1)
    
    # Get configuration
    repo_url = os.getenv("REPO_URL")
    if not repo_url:
        print("✗ REPO_URL not set in .env")
        sys.exit(1)

    clone_to_local = os.getenv("CLONE_LOCAL") or "cloned_repo"
    repo_path = PROJECT_ROOT / clone_to_local
    
    json_spec_file = os.getenv("JSON_SPEC_FILE") or str(PROJECT_ROOT / "actionable_item.json")
    
    if not Path(json_spec_file).exists():
        print(f"✗ JSON specification file not found: {json_spec_file}")
        sys.exit(1)

    if not repo_path.exists():
        print(f"✗ Repository not found: {repo_path}")
        print(f"Please run 'python core/taggingSuggestion.py' first to clone the repository.")
        sys.exit(1)

    print("=" * 70)
    print(" Smart Agentic Tagging System - LLM-Aware Framework")
    print("=" * 70)
    print(f"• JSON Spec      : {json_spec_file}")
    print(f"• Repo Path      : {repo_path}")
    print(f"• Vegas LLM      : Available (Framework-aware mode)")
    print("")

    # Step 1: Load tagging report
    report_file = OUTPUTS_DIR / "tagging_report.json"
    if not report_file.exists():
        print(f"✗ Tagging report not found: {report_file}")
        print("Please run 'python core/taggingSuggestion.py' first")
        sys.exit(1)

    print(f"📖 Loading report: {report_file}")
    with open(report_file, 'r', encoding='utf-8') as f:
        tagging_report = json.load(f)

    # Step 2: Convert to smart apply format
    print("🔄 Converting to smart apply format...")
    apply_plan = convert_report_to_apply_format(tagging_report, str(repo_path))
    
    # Save the apply plan for reference
    apply_plan_path = OUTPUTS_DIR / "apply_plan_smart.json"
    with open(apply_plan_path, 'w', encoding='utf-8') as f:
        json.dump(apply_plan, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Apply plan saved: {apply_plan_path}")
    
    # Step 3: Display summary
    items_count = len(apply_plan.get("items", []))
    print(f"📊 Items to process: {items_count}")
    
    if items_count == 0:
        print("⚠️  No items to apply. Check your JSON specification.")
        return
    
    # Step 4: Apply tagging using SMART Vegas LLM (with framework context)
    print("")
    print("=" * 70)
    print(" Applying Tags with SMART Vegas LLM (Framework-Aware)")
    print("=" * 70)
    print("🎯 LLM will:")
    print("   1. Read the ACTUAL Tagging framework code")
    print("   2. Understand available functions and parameters")
    print("   3. Intelligently decide imports, hooks, and calls")
    print("   4. NO hardcoded patterns - framework-driven decisions")
    print("")

    try:
        ok, fail, stats = ai_apply_from_json_smart(
            apply_plan_path,
            repo_path,
            model="vegas",
            dry_run=False,
            skip_if_tagged=True
        )
    except Exception as e:
        print(f"\n✗ Error during application: {e}")
        import traceback
        traceback.print_exc()
        raise

    # Step 5: Summary
    print("")
    print("=" * 70)
    print("Tracking Code Application Summary")
    print("=" * 70)
    print(f"✓ Successfully applied    : {ok}")
    print(f"✗ Failed                 : {fail}")
    print(f"⊘ Skipped (already tagged): {stats.get('skipped_already_tagged', 0)}")
    print("")
    print(f"📊 Tracking Statistics:")
    print(f"   • Imports added   : {stats.get('import_added', 0)}")
    print(f"   • Hooks added     : {stats.get('hook_added', 0)}")
    print(f"   • Calls added     : {stats.get('tracking_added', 0)}")
    
    if fail == 0:
        print("\n✓ All files tagged successfully!")
        print(f"  Backups saved with .taggingai.bak extension")
    else:
        print(f"\n⚠️  {fail} items failed to apply. Review apply_log_smart.json for details.")
    
    print("")
    print("=" * 70)
    print("Tracking Code Outputs")
    print("=" * 70)
    print(f"• Apply Plan     : {apply_plan_path}")
    print(f"• Apply Log      : {OUTPUTS_DIR / 'apply_log_smart.json'}")
    print(f"• Repo Path      : {repo_path}")
    
    # Step 6: Apply data-track attributes (NEW - Unified Pipeline)
    print("")
    print("=" * 70)
    print(" PHASE 2: Applying Data-Track Attributes")
    print("=" * 70)
    
    if DATA_TRACK_AVAILABLE:
        try:
            print("🚀 Starting data-track attribute application...")
            print("   (This adds semantic data-track attributes to interactive elements)")
            print("")
            
            dt_success, dt_fail, dt_stats = apply_data_track_attributes_smart(
                tagging_report_path=report_file,
                repo_root=repo_path,
                use_llm=bool(os.getenv("VEGAS_API_KEY")),
                dry_run=False,
                skip_if_already=True
            )
            
            print("")
            print("=" * 70)
            print("Data-Track Application Summary")
            print("=" * 70)
            print(f"✓ Files processed        : {dt_stats.get('processed', 0)}")
            print(f"✓ Successfully modified  : {dt_success}")
            print(f"✗ Failed                 : {dt_fail}")
            print(f"📊 Elements processed    : {dt_stats.get('total_elements_found', 0)}")
            print(f"📊 Data-track added      : {dt_stats.get('total_elements_modified', 0)}")
            print(f"⊘ Elements skipped       : {dt_stats.get('total_elements_skipped', 0)}")
            
            if dt_fail == 0:
                print("\n✓ Data-track attributes applied successfully!")
                print(f"  Backups saved with .datatrack.bak extension")
            else:
                print(f"\n⚠️  {dt_fail} files had issues. Review data_track_report.json for details.")
            
            print("")
            print("=" * 70)
            print("Data-Track Outputs")
            print("=" * 70)
            print(f"• Data-Track Report      : {OUTPUTS_DIR / 'data_track_report.json'}")
            
        except Exception as e:
            print(f"\n⚠️  Data-track application error: {e}")
            print("   (Tracking code was applied successfully)")
    else:
        print("⚠️  Data-track module not available")
        print("   Install it to automatically add data-track attributes")
    
    # Step 7: Final summary
    print("")
    print("=" * 70)
    print("UNIFIED PIPELINE COMPLETE ✓")
    print("=" * 70)
    print("")
    print("✅ Phase 1: Tracking Code Applied")
    print(f"   └─ Files: {ok} success, {fail} failed")
    
    if DATA_TRACK_AVAILABLE:
        print("")
        print("✅ Phase 2: Data-Track Attributes Applied")
        print(f"   └─ Files: {dt_success} success, {dt_fail} failed")
        print(f"   └─ Elements: {dt_stats.get('total_elements_modified', 0)} modified")
    
    print("")
    print("📂 All outputs saved in:", OUTPUTS_DIR)
    print("✓ Complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
