"""
Improved Apply Tagging Agent - Uses Smart Prompt Builder

This version:
1. Reads the Tagging framework
2. Passes it to LLM context
3. Lets LLM decide what imports/calls to add
4. Pre-checks for existing tagging (idempotency)
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import json
import re

from tools.vegas_llm_utils import VegasLLMWrapper
from tools.smart_prompt_builder import SmartPromptBuilder


def _read_text(p: Path) -> str:
    """Safely read file"""
    return p.read_text(encoding="utf-8")


def _write_text(p: Path, text: str):
    """Safely write file"""
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="")


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM response"""
    if not text:
        return {}
    
    try:
        return json.loads(text)
    except Exception:
        pass
    
    # Try to find JSON in response
    start = text.find("{")
    if start == -1:
        return {}
    
    # Find matching closing brace
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i+1])
                except:
                    pass
    
    return {}


def check_tagging_with_llm(
    client: VegasLLMWrapper,
    framework_content: str,
    target_file_content: str,
    tracking_function: str,
    instruction: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Use LLM to intelligently detect if tagging already exists
    
    LLM reads:
    1. Tagging framework (what functions exist)
    2. Target file (what's currently there)
    3. Instruction (what we want to add)
    
    LLM decides: "Is this tagging already present?"
    
    Returns:
        (already_tagged: bool, reason: str)
    """
    
    prompt = f"""You are a code analysis expert.

## TAGGING FRAMEWORK
This is the Tagging framework that defines available functions:

```javascript
{framework_content}
```

## TARGET FILE
This is the file we want to add tagging to:

```javascript
{target_file_content}
```

## TASK
Analyze if the following tracking is ALREADY present in the target file:

Function: {tracking_function}
Instruction: {json.dumps(instruction, indent=2)}

## DECISION RULES
- Look for calls to: {tracking_function}
- Check if it matches the intended purpose
- Consider different code patterns and styles
- Be strict: Only return true if tracking is clearly already there

## ANSWER
Return ONLY valid JSON (no markdown, no explanation):
{{
  "already_tagged": true/false,
  "reason": "brief explanation"
}}

For example:
{{
  "already_tagged": true,
  "reason": "trackPageLoad already called in useEffect with correct parameters"
}}

or

{{
  "already_tagged": false,
  "reason": "No trackPageLoad found in file"
}}
"""
    
    try:
        with open("prompt.txt", 'w', encoding='utf-8') as f:
            f.write(prompt)
        response = client.invoke(prompt)
        result = _extract_json(response)
        
        if not result:
            return (False, "Could not parse LLM response - assuming needs tagging")
        
        already_tagged = result.get("already_tagged", False)
        reason = result.get("reason", "LLM decision")
        
        return (already_tagged, reason)
        
    except Exception as e:
        print(f"  ⚠️  LLM check failed ({e}), proceeding with tagging")
        return (False, f"LLM check failed: {str(e)}")


def has_tagging_already_simple(file_content: str, tracking_function: str) -> bool:
    """
    Fast simple check: Does the function name appear at all?
    This is a quick pre-filter before LLM check.
    """
    return tracking_function in file_content


def _ai_edit_file_smart(
    client: VegasLLMWrapper,
    prompt_builder: SmartPromptBuilder,
    target_file_path: str,
    file_content: str,
    instruction: Dict[str, Any],
    anchor_line: int,
    snippet: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call LLM with smart prompt that includes Tagging framework context
    """
    
    # Build intelligent prompt
    prompt = prompt_builder.build_intelligent_prompt(
        target_file_path=target_file_path,
        target_file_content=file_content,
        instruction=instruction,
        anchor_line=anchor_line,
        snippet=snippet
    )
    
    try:
        # Call Vegas LLM
        with open("smart_prompt.txt", 'w', encoding='utf-8') as f:
            f.write(prompt)
        response_text = client.invoke(prompt)
        
        # Extract JSON
        result = _extract_json(response_text)
        
        # Validate response
        if not result:
            return {
                "applied": False,
                "reason": "Could not extract JSON from LLM response",
                "updated_file": file_content,
                "import_added": False,
                "hook_added": False,
                "tracking_added": False
            }
        
        # Ensure updated_file is present
        if "updated_file" not in result:
            result["updated_file"] = file_content
        
        return result
        
    except Exception as e:
        return {
            "applied": False,
            "reason": f"LLM error: {str(e)}",
            "updated_file": file_content,
            "import_added": False,
            "hook_added": False,
            "tracking_added": False
        }


def ai_apply_from_json_smart(
    json_path: str | Path,
    repo_root: str | Path,
    model: str = "vegas",
    dry_run: bool = False,
    skip_if_tagged: bool = True,  # NEW: Skip already-tagged files
) -> Tuple[int, int, Dict[str, Any]]:
    """
    Improved version: Read Tagging framework, let LLM decide
    
    Args:
        json_path: Path to apply_plan.json
        repo_root: Repository root
        model: LLM model to use
        dry_run: Simulate without writing
        skip_if_tagged: Skip files that already have tagging (idempotency)
    
    Returns:
        (success_count, fail_count, statistics_dict)
    """
    
    client = VegasLLMWrapper()
    js = Path(json_path).resolve()
    repo = Path(str(repo_root)).resolve()
    
    # Initialize prompt builder with repo context
    prompt_builder = SmartPromptBuilder(str(repo))
    
    # Load plan
    with open(js, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle three formats:
    # 1. [...] - direct array format (NEW - PREFERRED)
    # 2. {"items": [...]} - flat array with "items" key
    # 3. {"file:lineNumbers": {...}} - hierarchical object format
    
    if isinstance(data, list):
        # Format 1: Direct array format (array of items)
        items = data
    elif isinstance(data, dict) and "items" in data:
        # Format 2: Flat array with "items" key
        items = data.get("items") or []
    elif isinstance(data, dict):
        # Format 3: Hierarchical object with file:lineNumbers as keys
        # Convert to flat items list
        items = []
        for key, item_data in data.items():
            if isinstance(item_data, dict):
                # Add file info from key
                item_data_copy = item_data.copy()
                item_data_copy["_key"] = key  # Store original key for reference
                
                # Parse file:lineNumbers format if present
                if ":" in key:
                    file_part, line_part = key.rsplit(":", 1)
                    item_data_copy["file"] = file_part
                    item_data_copy["file_path"] = file_part
                    item_data_copy["_lines"] = line_part
                else:
                    item_data_copy["file"] = key
                    item_data_copy["file_path"] = key
                
                items.append(item_data_copy)
    else:
        items = []
    
    if not items:
        print(f"✗ No items found in {js}")
        return (0, 0, {"error": "No items"})
    
    logs: List[Dict[str, Any]] = []
    ok = fail = skipped = 0
    
    stats = {
        "total_items": len(items),
        "processed": 0,
        "success": 0,
        "failed": 0,
        "skipped_already_tagged": 0,
        "import_added": 0,
        "hook_added": 0,
        "tracking_added": 0,
    }
    
    for idx, it in enumerate(items, 1):
        print(f"\n[{idx}/{len(items)}] Processing...")
        
        # Resolve target file
        file_hint = it.get("file") or it.get("file_path")
        print(file_hint)
        if not file_hint:
            print(f"✗ No file path in item")
            fail += 1
            stats["failed"] += 1
            continue
        
        target = Path(file_hint)
        if not target.is_absolute():
            target = (repo / target).resolve()
        
        if not target.exists():
            print(f"✗ File not found: {target}")
            fail += 1
            stats["failed"] += 1
            continue
        
        try:
            print(target)

            src = _read_text(target)
            with open(f"current_file{idx}.txt", 'w', encoding='utf-8') as f:
                f.write(src)
            
        except Exception as e:
            print(f"✗ Read failed: {e}")
            fail += 1
            stats["failed"] += 1
            continue
        
        # NEW: Pre-check for existing tagging (idempotency) - SMART CHECK
        tracking_func = it.get("suggested_event_name") or it.get("event") or "trackPageLoad"
        
        if skip_if_tagged:
            # STEP 1: Quick filter - is function name even present?
            if not has_tagging_already_simple(src, tracking_func):
                print(f"  ℹ️  Function '{tracking_func}' not found, will proceed to LLM")
            else:
                # STEP 2: Use LLM to intelligently check if already tagged
                print(f"  🔍 Checking if '{tracking_func}' is already properly tagged (using LLM)...")
                
                # Read framework for context
                framework_path = repo / "src" / "pages" / "ExpressStore" / "Tagging" / "index.js"
                framework_content = _read_text(framework_path) if framework_path.exists() else ""
                
                # Get instruction details
                instruction = {
                    "action": (it.get("action") or "").lower().strip() or "page_load",
                    "event": tracking_func,
                    "params": it.get("suggested_params") or it.get("params") or {}
                }
                
                # LLM check: Pass both framework + target file
                already_tagged, reason = check_tagging_with_llm(
                    client=client,
                    framework_content=framework_content,
                    target_file_content=src,
                    tracking_function=tracking_func,
                    instruction=instruction
                )
                
                if already_tagged:
                    print(f"⊘ SKIPPED: {reason}")
                    logs.append({
                        **it,
                        "result": {
                            "applied": False,
                            "reason": f"Skipped (LLM detected): {reason}",
                            "skipped": True
                        }
                    })
                    skipped += 1
                    stats["skipped_already_tagged"] += 1
                    continue
                else:
                    print(f"  ✓ LLM confirmed: {reason} - Will apply tagging")
        
        # Gather instruction
        action = (it.get("action") or "").lower().strip() or "page_load"
        event = tracking_func
        params = it.get("suggested_params") or it.get("params") or {}
        snippet = it.get("snippet")
        anchor = int((it.get("top_match") or {}).get("line") or 1)
        
        print(f"  File: {target.name}")
        print(f"  Event: {event}")
        print(f"  Action: {action}")
        
        # Call improved LLM with framework context
        
        result = _ai_edit_file_smart(
            client=client,
            prompt_builder=prompt_builder,
            target_file_path=str(target.relative_to(repo)),
            file_content=src,
            instruction={
                "action": action,
                "event": event,
                "params": params
            },
            anchor_line=anchor,
            snippet=snippet
        )
        
        applied = result.get("applied", False)
        reason = result.get("reason", "No changes")
        new_src = result.get("updated_file", src)
        
        print(f"  Result: {reason}")
        
        # Track what was added
        if result.get("import_added"):
            stats["import_added"] += 1
        if result.get("hook_added"):
            stats["hook_added"] += 1
        if result.get("tracking_added"):
            stats["tracking_added"] += 1
        
        # No changes
        if not applied or new_src == src:
            print(f"  ⊘ No changes needed")
            logs.append({**it, "result": {"applied": False, "reason": reason}})
            ok += 1
            stats["processed"] += 1
            continue
        
        # Dry run
        if dry_run:
            print(f"  [DRY-RUN] Would update file")
            logs.append({**it, "result": {"applied": True, "reason": f"dry_run: {reason}"}})
            ok += 1
            stats["processed"] += 1
            continue
        
        # Write to file
        try:
            backup = target.with_suffix(target.suffix + ".taggingai.bak")
            if not backup.exists():
                _write_text(backup, src)
            _write_text(target, new_src)
            print(f"  ✓ Updated successfully")
            logs.append({
                **it,
                "result": {
                    "applied": True,
                    "reason": reason,
                    "backup": str(backup.name)
                }
            })
            ok += 1
            stats["success"] += 1
            stats["processed"] += 1
        except Exception as e:
            print(f"  ✗ Write failed: {e}")
            fail += 1
            stats["failed"] += 1
    
    # Save logs
    try:
        log_file = js.parent / "apply_log_smart.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                "logs": logs,
                "stats": stats
            }, f, indent=2, ensure_ascii=False)
        print(f"\n📋 Logs saved: {log_file}")
    except Exception:
        pass
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Success:              {ok}")
    print(f"✗ Failed:               {fail}")
    print(f"⊘ Skipped (already):    {skipped}")
    print(f"  Imports added:        {stats['import_added']}")
    print(f"  Hooks added:          {stats['hook_added']}")
    print(f"  Tracking calls added: {stats['tracking_added']}")
    print()
    
    return (ok, fail, stats)


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    load_dotenv()
    
    ap = argparse.ArgumentParser(description="Smart AI Tagging Applier")
    ap.add_argument("--json", default="outputs/apply_plan.json")
    ap.add_argument("--repo", default="../cloned_repo")
    ap.add_argument("--model", default="vegas")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-skip", action="store_true", help="Don't skip already-tagged files")
    
    args = ap.parse_args()
    
    ok, fail, stats = ai_apply_from_json_smart(
        json_path=args.json,
        repo_root=args.repo,
        model=args.model,
        dry_run=args.dry_run,
        skip_if_tagged=not args.no_skip
    )
    
    print(f"\nFinal Result: {ok} processed, {fail} failed")
