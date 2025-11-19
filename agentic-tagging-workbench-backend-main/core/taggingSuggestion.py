# quick_start.py
import os
import sys
import time
from pathlib import Path
from contextlib import contextmanager
from dotenv import load_dotenv

from agents.agent import build_unified, write_outputs

from cloneRepo import clone_to_fixed_location as clone_repo_url

CORE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = CORE_DIR / "outputs"

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
    use_llm = bool(os.getenv("OPENAI_API_KEY"))

    # Resolve inputs
    excel_candidates = [
        os.getenv("TECHSPEC_PATH")
        # "TechSpec_Tagging.xlsx",
        # "techspec.xlsx",
    ]
    excel = next((p for p in excel_candidates if p and Path(p).exists()), None)
    if not excel:
        print("✗ Could not find a Tech Spec Excel file. Looked for:")
        for c in excel_candidates:
            if c:
                print(f"  - {c}")
        sys.exit(1)

    # repo = os.getenv("REPO_PATH")
    # if not Path(repo).exists():
    #     print(f"✗ React repo not found at: {repo}")
    #     sys.exit(1)

    repo_url    = os.getenv("REPO_URL")        # preferred
    repo_branch = os.getenv("REPO_BRANCH") or None   # optional
    # clone_base  = Path(os.getenv("CLONE_BASE", str(Path.home() / "ATTagger" / "Test"))).expanduser().resolve()
    val = os.environ.get("CLONE_BASE")
    if not val:
       raise RuntimeError(
          "CLONE_BASE is not set. Add `CLONE_BASE=${HOME}/ATTagger/Test` (or an absolute path) to your .env"
     )
   # expand ${HOME} / ~ and resolve to an absolute path
    clone_base = Path(os.path.expandvars(val)).expanduser().resolve()

    # legacy_repo = os.getenv("REPO_PATH") 


    print("==========================================")
    print(" Agentic Tagging — Unified Suggestions Run ")
    print("==========================================")
    print(f"• Tech Spec : {excel}")
    # print(f"• Repo      : {repo}")

    print(f"• Repo URL  : {repo_url}")
    print(f"• Branch    : {repo_branch or '(default)'}")
    print(f"• CloneBase : {clone_base}")
    #    print(f"• Repo      : {legacy_repo}")
    print(f"• OpenAI    : {'ON (LLM + embeddings)' if use_llm else 'OFF (heuristics only)'}")
    print("")

    with step("Cloning repository"):
    # If your clone function doesn't accept branch/clone_base, keep only repo_url.
         repo_path = Path(clone_repo_url(repo_url)).resolve()

# Validate cloned path
    if not repo_path.exists() or not repo_path.is_dir():
      print(f"✗ Clone failed or bad path: {repo_path}")
      sys.exit(1)

# (debug) show the path we will scan
    print(f"→ Using repo_path: {repo_path}")

    # --- persist the final repo path so the API/UI can read it later
# Prefer an explicit env var (if your API passed one), else default to outputs/.last_repo_root
    # target_path = os.environ.get("LAST_REPO_ROOT_FILE")
    # if not target_path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    target_path = str(OUTPUTS_DIR / ".last_repo_root")

    p = Path(target_path)
    p.parent.mkdir(parents=True, exist_ok=True)

# atomic-ish write to avoid partial reads
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(str(repo_path), encoding="utf-8")
    tmp.replace(p)

# optional: stdout fallback for parsers/logs
    print(f"CLONED_TO: {repo_path}")

    # Build unified output (parsing spec, scanning repo, mapping, LLM reasoning)
    with step("Analyzing Tech Spec + Scanning Repo + Generating Suggestions"):
        # unified = build_unified(excel, repo, use_llm=use_llm)
        unified = build_unified(excel, str(repo_path), use_llm=use_llm)

    # Write files
    with step("Writing outputs (JSON / Markdown / JS module if enabled)"):
        out = write_outputs(unified)

    # Summary
    items = len(unified.get("items", []))
    suggested = sum(1 for it in unified.get("items", []) if it.get("top_match"))
    print("")
    print("Summary")
    print("-------")
    print(f"• Items processed : {items}")
    print(f"• With suggestions: {suggested}/{items}")
    print("")
    print("Outputs")
    print("-------")
    print(f"• JSON     : {out.get('json')}")
    print(f"• Markdown : {out.get('md')}")
    if out.get("js"):
        print(f"• JS module: {out.get('js')}")
    print("")
    print("Done ")

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
