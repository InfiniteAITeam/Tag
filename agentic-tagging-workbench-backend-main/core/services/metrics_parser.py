# services/metrics_parser.py
import re
from collections import Counter
from pathlib import Path

_UPDATED_LINE = re.compile(
    r"^\s*✓ Updated:\s+(?P<file>.+?)\s*\((?P<msg>.*?)\)\s*\(backup:\s*(?P<bak>[^)]+)\)", re.M
)
_RESULT_LINE = re.compile(r"Result:\s*(?P<proc>\d+)\s+items processed,\s*(?P<fail>\d+)\s+failed\.", re.M)

def parse_apply_stdout(stdout: str) -> dict:
    files, backups, updates = [], [], []
    for m in _UPDATED_LINE.finditer(stdout or ""):
        f = m.group("file").strip()
        files.append(f)
        backups.append(m.group("bak").strip())
        updates.append({"file": f, "message": m.group("msg").strip()})

    res = _RESULT_LINE.search(stdout or "")
    items_processed = int(res.group("proc")) if res else len(files)
    failed = int(res.group("fail")) if res else 0

    by_ext = Counter((Path(f).suffix.lower() or "(noext)") for f in files)
    by_dir = Counter(str(Path(f).parent) for f in files)

    return {
        "items_processed": items_processed,
        "failed": failed,
        "files_modified": len(set(files)),
        "backups_created": len(set(backups)),
        "by_extension": dict(by_ext),
        "by_directory": dict(by_dir),
        "updates": updates,
    }
