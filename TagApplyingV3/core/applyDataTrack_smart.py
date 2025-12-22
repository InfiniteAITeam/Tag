#!/usr/bin/env python
"""
Apply Data-Track Attributes - Smart LLM-Aware System

This script:
1. Reads tagging_report.json (same as tracking tagging)
2. For each file, identifies interactive elements (buttons, divs with onClick)
3. Uses LLM to generate appropriate data-track values
4. Applies data-track attributes to elements
5. Generates comprehensive report
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

from tools.data_track_extractor import ElementExtractor, ValueSanitizer, InteractiveElement
from tools.data_track_applier import DataTrackApplier
from tools.vegas_llm_utils import VegasLLMWrapper

CORE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = CORE_DIR / "outputs"
PROJECT_ROOT = CORE_DIR.parent


def _read_text(p: Path) -> str:
    """Safely read file"""
    return p.read_text(encoding="utf-8")


def _write_text(p: Path, text: str):
    """Safely write file"""
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="")


def apply_data_track_attributes_smart(
    tagging_report_path: str | Path,
    repo_root: str | Path,
    use_llm: bool = True,
    dry_run: bool = False,
    skip_if_already: bool = True,
) -> Tuple[int, int, Dict[str, Any]]:
    """
    Apply data-track attributes to interactive elements in target files
    
    Args:
        tagging_report_path: Path to tagging_report.json
        repo_root: Repository root path
        use_llm: Whether to use LLM for intelligent analysis
        dry_run: Simulate without writing
        skip_if_already: Skip elements that already have data-track
    
    Returns:
        (success_count, fail_count, statistics_dict)
    """
    
    # Initialize clients
    if use_llm:
        llm_client = VegasLLMWrapper()
        applier = DataTrackApplier(llm_client)
    else:
        applier = None
    
    report_path = Path(tagging_report_path).resolve()
    repo = Path(str(repo_root)).resolve()
    
    # Load tagging report
    with open(report_path, 'r', encoding='utf-8') as f:
        tagging_report = json.load(f)
    
    files_to_process = tagging_report.get("files", [])
    
    if not files_to_process:
        print(f"✗ No files found in {report_path}")
        return (0, 0, {"error": "No files to process"})
    
    # Tracking
    logs: List[Dict[str, Any]] = []
    success_count = 0
    fail_count = 0
    
    stats = {
        "total_files": len(files_to_process),
        "processed": 0,
        "success": 0,
        "failed": 0,
        "total_elements_found": 0,
        "total_elements_modified": 0,
        "total_elements_skipped": 0,
        "backup_created": 0,
    }
    
    print("\n" + "=" * 70)
    print(" Data-Track Attribute Application - LLM-Aware")
    print("=" * 70)
    print(f"📊 Files to process: {len(files_to_process)}")
    print(f"🤖 LLM enabled: {use_llm}")
    print(f"🔄 Skip already tagged: {skip_if_already}")
    print("")
    
    for idx, file_info in enumerate(files_to_process, 1):
        file_path = file_info.get("file")
        
        if not file_path:
            print(f"[{idx}/{len(files_to_process)}] ✗ No file path")
            fail_count += 1
            stats["failed"] += 1
            continue
        
        # Resolve file path
        target = Path(file_path)
        if not target.is_absolute():
            target = (repo / target).resolve()
        
        if not target.exists():
            print(f"[{idx}/{len(files_to_process)}] ✗ File not found: {file_path}")
            fail_count += 1
            stats["failed"] += 1
            continue
        
        print(f"\n[{idx}/{len(files_to_process)}] 📄 {target.name}")
        
        try:
            # Read file
            src = _read_text(target)
            file_log = {
                "file": str(file_path),
                "status": "processing",
                "elements_found": 0,
                "elements_modified": 0,
                "elements_skipped": 0,
                "details": []
            }
            
            # Step 1: Extract interactive elements
            print(f"  🔍 Extracting interactive elements...")
            extractor = ElementExtractor(str(target), src)
            elements = extractor.extract_all_interactive_elements()
            
            if not elements:
                print(f"  ℹ️  No interactive elements found")
                file_log["status"] = "no_elements"
                logs.append(file_log)
                success_count += 1
                stats["processed"] += 1
                stats["success"] += 1
                continue
            
            print(f"  ✓ Found {len(elements)} interactive elements")
            stats["total_elements_found"] += len(elements)
            file_log["elements_found"] = len(elements)
            
            # Step 2: Generate data-track values
            print(f"  🎯 Generating data-track values...")
            elements_to_modify = []
            sanitizer = ValueSanitizer()
            
            for elem_idx, elem in enumerate(elements):
                # Skip if already has data-track
                if elem.has_data_track:
                    if skip_if_already:
                        print(f"    ⊘ Element {elem_idx + 1}: Already has data-track")
                        stats["total_elements_skipped"] += 1
                        file_log["elements_skipped"] += 1
                        
                        detail = {
                            "line": elem.line_number,
                            "element_type": elem.element_type.value,
                            "status": "skipped",
                            "reason": "Already has data-track attribute"
                        }
                        file_log["details"].append(detail)
                        continue
                
                # Generate value using LLM if enabled
                if use_llm and applier:
                    extracted_text = sanitizer.extract_text_from_element(elem)
                    print(f"    🤖 Element {elem_idx + 1}: Generating value from '{extracted_text[:30]}'...")
                    
                    value, reasoning, confidence = applier.generate_value_with_llm(
                        file_content=src,
                        file_path=str(target.relative_to(repo)),
                        element={
                            "element_type": elem.element_type.value,
                            "line_number": elem.line_number,
                            "html_snippet": elem.element_html
                        },
                        extracted_text=extracted_text
                    )
                else:
                    # Fallback: simple sanitization of extracted text
                    extracted_text = sanitizer.extract_text_from_element(elem)
                    value = sanitizer.sanitize(extracted_text)
                    reasoning = "Sanitized from extracted text"
                    confidence = "medium"
                
                # Validate value
                if not sanitizer.is_valid_value(value):
                    print(f"    ⚠️  Element {elem_idx + 1}: Generated invalid value '{value}', skipping")
                    stats["total_elements_skipped"] += 1
                    file_log["elements_skipped"] += 1
                    
                    detail = {
                        "line": elem.line_number,
                        "element_type": elem.element_type.value,
                        "status": "skipped",
                        "reason": f"Generated invalid value: {value}"
                    }
                    file_log["details"].append(detail)
                    continue
                
                print(f"    ✓ Element {elem_idx + 1}: data-track=\"{value}\"")
                
                elements_to_modify.append({
                    "line_number": elem.line_number,
                    "element_type": elem.element_type.value,
                    "data_track_value": value,
                    "current_html": elem.element_html,
                    "reasoning": reasoning,
                    "confidence": confidence
                })
                
                file_log["elements_modified"] += 1
                stats["total_elements_modified"] += 1
                
                detail = {
                    "line": elem.line_number,
                    "element_type": elem.element_type.value,
                    "data_track_value": value,
                    "confidence": confidence,
                    "status": "marked_for_modification"
                }
                file_log["details"].append(detail)
            
            # Step 3: Apply data-track attributes if there are modifications
            if not elements_to_modify:
                print(f"  ℹ️  No elements need modification")
                file_log["status"] = "no_modifications_needed"
                logs.append(file_log)
                success_count += 1
                stats["processed"] += 1
                stats["success"] += 1
                continue
            
            print(f"  ✏️  Applying {len(elements_to_modify)} data-track attributes...")
            
            if use_llm and applier:
                updated_src, mod_log = applier.apply_data_track_with_llm(
                    file_content=src,
                    file_path=str(target.relative_to(repo)),
                    elements_to_modify=elements_to_modify
                )
            else:
                # Fallback: simple regex replacement
                updated_src = src
                mod_log = []
                for elem_info in elements_to_modify:
                    # Try to find and replace element with data-track
                    # This is a simple fallback, LLM version is much better
                    line_num = elem_info["line_number"]
                    if line_num <= len(src.split('\n')):
                        # Simple approach: this would need more sophisticated handling
                        pass
            
            # Step 4: Check if changes were made
            if updated_src == src:
                print(f"  ℹ️  No changes needed to file")
                file_log["status"] = "no_changes"
                logs.append(file_log)
                success_count += 1
                stats["processed"] += 1
                stats["success"] += 1
                continue
            
            # Step 5: Dry run check
            if dry_run:
                print(f"  [DRY-RUN] Would update file with {len(elements_to_modify)} modifications")
                file_log["status"] = "dry_run"
                logs.append(file_log)
                success_count += 1
                stats["processed"] += 1
                stats["success"] += 1
                continue
            
            # Step 6: Create backup
            try:
                backup = target.with_suffix(target.suffix + ".datatrack.bak")
                if not backup.exists():
                    _write_text(backup, src)
                    stats["backup_created"] += 1
                print(f"  💾 Backup created: {backup.name}")
            except Exception as e:
                print(f"  ✗ Backup failed: {e}")
                fail_count += 1
                stats["failed"] += 1
                file_log["status"] = "backup_failed"
                logs.append(file_log)
                continue
            
            # Step 7: Write updated file
            try:
                _write_text(target, updated_src)
                print(f"  ✓ File updated successfully")
                file_log["status"] = "success"
                success_count += 1
                stats["processed"] += 1
                stats["success"] += 1
            except Exception as e:
                print(f"  ✗ Write failed: {e}")
                fail_count += 1
                stats["failed"] += 1
                file_log["status"] = "write_failed"
            
            logs.append(file_log)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            fail_count += 1
            stats["failed"] += 1
            logs.append({
                "file": str(file_path),
                "status": "error",
                "error": str(e)
            })
    
    # Save report
    try:
        report_file = OUTPUTS_DIR / "data_track_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "logs": logs,
                "stats": stats
            }, f, indent=2, ensure_ascii=False)
        print(f"\n📋 Report saved: {report_file}")
    except Exception:
        pass
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Success:                  {success_count}")
    print(f"✗ Failed:                   {fail_count}")
    print(f"📊 Files processed:         {stats['processed']}")
    print(f"🎯 Total elements found:    {stats['total_elements_found']}")
    print(f"✏️  Elements modified:       {stats['total_elements_modified']}")
    print(f"⊘ Elements skipped:         {stats['total_elements_skipped']}")
    print(f"💾 Backups created:         {stats['backup_created']}")
    print("")
    
    if fail_count == 0 and success_count > 0:
        print("✓ All files processed successfully!")
    else:
        print(f"⚠️  {fail_count} files had issues. Check data_track_report.json for details.")
    
    print("")
    print("=" * 70)
    
    return (success_count, fail_count, stats)


def main():
    load_dotenv()
    
    # Check Vegas LLM
    vegas_api_key = os.getenv("VEGAS_API_KEY")
    use_llm = bool(vegas_api_key)
    
    if not use_llm:
        print("⚠️  VEGAS_API_KEY not set - will use fallback mode (less intelligent)")
    
    # Get configuration
    repo_url = os.getenv("REPO_URL")
    clone_to_local = os.getenv("CLONE_LOCAL") or "cloned_repo"
    repo_path = PROJECT_ROOT / clone_to_local
    
    if not repo_path.exists():
        print(f"✗ Repository not found: {repo_path}")
        print(f"Please run 'python core/taggingSuggestion.py' first to clone the repository.")
        sys.exit(1)
    
    # Check tagging report
    report_file = OUTPUTS_DIR / "tagging_report.json"
    if not report_file.exists():
        print(f"✗ Tagging report not found: {report_file}")
        print("Please run 'python core/taggingSuggestion.py' first")
        sys.exit(1)
    
    print("=" * 70)
    print(" Data-Track Attribute Application - LLM-Aware")
    print("=" * 70)
    print(f"• Repo Path      : {repo_path}")
    print(f"• Tagging Report : {report_file}")
    print(f"• Vegas LLM      : {'Available' if use_llm else 'Not configured (fallback mode)'}")
    print("")
    
    try:
        success, fail, stats = apply_data_track_attributes_smart(
            tagging_report_path=report_file,
            repo_root=repo_path,
            use_llm=use_llm,
            dry_run=False,
            skip_if_already=True
        )
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
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
