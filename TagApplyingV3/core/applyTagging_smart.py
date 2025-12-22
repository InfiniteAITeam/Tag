#!/usr/bin/env python
"""
Smart Apply Tagging - Orchestrates the new smart LLM-aware tagging system

This script:
1. Reads tagging_report.json (from taggingSuggestion.py)
2. Converts it to apply_plan.json format (compatible with new smart agent)
3. Calls the new smart agent which:
   - Reads the ACTUAL Tagging framework
   - Passes it to LLM for intelligent decisions
   - Lets LLM figure out imports, hooks, and calls (no hardcoding)
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

from applyTaggingAgent_smart import ai_apply_from_json_smart

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
    print("Summary")
    print("=" * 70)
    print(f"✓ Successfully applied    : {ok}")
    print(f"✗ Failed                 : {fail}")
    print(f"⊘ Skipped (already tagged): {stats.get('skipped_already_tagged', 0)}")
    print("")
    print(f"📊 Statistics:")
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
    print("Outputs")
    print("=" * 70)
    print(f"• Apply Plan     : {apply_plan_path}")
    print(f"• Apply Log      : {OUTPUTS_DIR / 'apply_log_smart.json'}")
    print(f"• Repo Path      : {repo_path}")
    print("")
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
