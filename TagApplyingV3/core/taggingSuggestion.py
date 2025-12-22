# quick_start.py - Agentic Tagging System
# This script orchestrates the complete tagging workflow using JSON specifications
import os
import sys
import time
import json
import shutil
import subprocess
from pathlib import Path
from contextlib import contextmanager
from dotenv import load_dotenv

from tools.taggingApplier import analyze_tagging_requirements, get_tagging_prompt
from tools.tagging_prompts import get_system_prompt, get_prompt_for_event_type, get_user_prompt_for_file
from tools.tagging_validator import validate_tagging_code, get_validation_report

CORE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = CORE_DIR / "outputs"
PROJECT_ROOT = CORE_DIR.parent

# ---------- tiny CLI UI helpers ----------
SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

class Spinner:
    def __init__(self, label: str):
        self.label = label
        self._running = False

    def start(self):
        self._running = True
        self._animate_start = time.perf_counter()
        i = 0
        while self._running:
            frame = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
            sys.stdout.write(f"\r{frame} {self.label} ")
            sys.stdout.flush()
            i += 1
            time.sleep(0.08)

    def stop(self, ok: bool = True):
        self._running = False
        elapsed = time.perf_counter() - self._animate_start
        icon = "✓" if ok else "✗"
        sys.stdout.write(f"\r{icon} {self.label}  ({elapsed:.1f}s)\n")
        sys.stdout.flush()

@contextmanager
def step(label: str):
    sp = Spinner(label)
    try:
        import threading
        t = threading.Thread(target=sp.start, daemon=True)
        t.start()
        yield sp
        sp.stop(ok=True)
    except Exception:
        sp.stop(ok=False)
        raise

# ---------- main ----------
def main():
    load_dotenv()
    use_llm = bool(os.getenv("VEGAS_API_KEY"))

    # Get configuration
    repo_url = os.getenv("REPO_URL")
    if not repo_url:
        print("✗ REPO_URL not set in .env")
        sys.exit(1)

    repo_branch = os.getenv("REPO_BRANCH") or None
    
    # Clone locally into a subfolder of this project (not CLONE_BASE)
    clone_to_local = os.getenv("CLONE_LOCAL") or "cloned_repo"
    repo_path = PROJECT_ROOT / clone_to_local
    
    # JSON Specification file (updated to use new actionable_item.json)
    json_spec_file = os.getenv("JSON_SPEC_FILE") or str(PROJECT_ROOT / "actionable_item.json")
    
    if not Path(json_spec_file).exists():
        print(f"✗ JSON specification file not found: {json_spec_file}")
        print(f"  Expected at: {json_spec_file}")
        sys.exit(1)

    print("=" * 50)
    print(" Agentic Tagging System - JSON Workflow")
    print("=" * 50)
    print(f"• JSON Spec      : {json_spec_file}")
    print(f"• Repo URL       : {repo_url}")
    print(f"• Branch         : {repo_branch or '(default)'}")
    print(f"• Clone To       : {repo_path}")
    print(f"• Vegas LLM      : {'ON' if use_llm else 'OFF'}")
    print("")

    # Step 1: Clone repository directly into project folder
    # COMMENTED OUT - Repository already cloned locally
    # with step("Cloning repository"):
    #     try:
    #         # Remove existing clone if it exists
    #         if repo_path.exists():
    #             shutil.rmtree(repo_path, ignore_errors=True)
            
    #         repo_path.parent.mkdir(parents=True, exist_ok=True)
            
    #         # Clone directly using git
    #         result = subprocess.run(
    #             ["git", "clone", repo_url, str(repo_path)],
    #             capture_output=True,
    #             text=True,
    #             timeout=300
    #         )
            
    #         if result.returncode != 0:
    #             print(f"\n✗ Git clone failed with status {result.returncode}")
    #             print(f"\nError output:")
    #             print(result.stderr)
    #             print(f"\nStandard output:")
    #             print(result.stdout)
                
    #             if "Permission denied" in result.stderr or "Authentication" in result.stderr:
    #                 print("\n⚠️  Authentication issue detected!")
    #                 print("   The repository requires credentials.")
    #                 print("   Options:")
    #                 print("   1. Use an SSH key configured for GitLab")
    #                 print("   2. Use git credential manager for HTTPS")
    #                 print("   3. Create a GitLab personal access token")
                
    #             raise RuntimeError(f"Git clone failed: {result.stderr}")
            
    #         # Setup tagging framework
    #         tagging_target = repo_path / "src" / "pages" / "ExpressStore" / "Tagging"
            # tagging_target.mkdir(parents=True, exist_ok=True)
    
            # Copy tagging files
            # tagging_files = ["index.js", "dlStructure.js"]
            # for file_name in tagging_files:
            #     source_file = PROJECT_ROOT / file_name
            #     target_file = tagging_target / file_name
            #     if source_file.exists():
            #         shutil.copy2(source_file, target_file)
        
        # except subprocess.TimeoutExpired:
        #     print("\n✗ Git clone timed out after 5 minutes")
        #     raise
        # except Exception as e:
        #     print(f"\n✗ Error during clone: {e}")
        #     raise

    # Verify repository path exists
    if not repo_path.exists() or not repo_path.is_dir():
        print(f"✗ Clone failed or bad path: {repo_path}")
        sys.exit(1)

    print(f"✓ Using repository at: {repo_path}")

    # Step 2: Analyze tagging requirements from JSON spec
    with step("Analyzing tagging requirements"):
        tagging_report = analyze_tagging_requirements(json_spec_file, str(repo_path))

    # Save tagging report
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    tagging_report_path = OUTPUTS_DIR / "tagging_report.json"
    with open(tagging_report_path, 'w', encoding='utf-8') as f:
        json.dump(tagging_report, f, indent=2)
    
    # Step 3: Generate LLM tagging prompt
    with step("Generating tagging instructions"):
        tagging_prompt = get_tagging_prompt(json_spec_file, str(repo_path))

    tagging_prompt_path = OUTPUTS_DIR / "tagging_prompt.txt"
    with open(tagging_prompt_path, 'w', encoding='utf-8') as f:
        f.write(tagging_prompt)

    # Save repo path for API access
    target_path = OUTPUTS_DIR / ".last_repo_root"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = target_path.with_suffix(target_path.suffix + ".tmp")
    tmp.write_text(str(repo_path), encoding="utf-8")
    tmp.replace(target_path)

    # Display summary
    files_to_tag = len(tagging_report.get("files", []))
    missing_files = len(tagging_report.get("missing_files", []))
    
    print("")
    print("=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"• Files to tag       : {files_to_tag}")
    print(f"• Missing files      : {missing_files}")
    print("")
    print("Outputs")
    print("=" * 50)
    print(f"• Tagging Report : {tagging_report_path}")
    print(f"• Tagging Prompt : {tagging_prompt_path}")
    print(f"• Repo Cloned To : {repo_path}")
    print("")
    print("✓ Complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(130)
    except Exception as e:
        # Show a concise error with a hint to enable verbose logs
        print(f"\n✗ Error: {e}")
        print("Hint: set more logs in your modules or run with environment-specific debug flags.")
        # raise
        sys.exit(1)
