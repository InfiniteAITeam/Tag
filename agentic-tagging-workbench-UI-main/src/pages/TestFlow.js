// src/pages/TestFlow.js
import React, { useRef, useState, useEffect } from "react";
import * as XLSX from "xlsx";
import "./testflow.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";


// Set FastAPI base
const DEFAULT_API = "http://127.0.0.1:8000";

export default function TestFlow({ apiBase = DEFAULT_API }) {
  const [step, setStep] = useState(1);
  const [done, setDone] = useState({ 1: false, 2: false, 3: false, 4: false });
  const [showActionsOnly, setShowActionsOnly] = useState(false);
  const [figmaImgUrl, setFigmaImgUrl] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [resolvedRepoPath, setResolvedRepoPath] = useState("");
  const [diffRepoRoot, setDiffRepoRoot] = useState("");
  const [applyLogPath, setApplyLogPath] = useState("");
  const WORKFLOW_TEXT = "Residential portal → Pay Rent → Monthly Payment";


  // Reusable ticker pusher (keeps last 6 items)
  const makePusher = (setArr) => (text, icon = "▶") =>
  setArr((arr) =>
    [...arr, { id: Date.now() + Math.random(), text, icon }].slice(-6)
  );
  // Apply Tagging popup state
  const [procApplyOpen, setProcApplyOpen] = useState(false);
  const [procApplyLines, setProcApplyLines] = useState([]);
  const [applyDone, setApplyDone] = useState(false);
  const pushApplyLoading = (line) =>
  setProcApplyLines((arr) =>
    [...arr, { id: Date.now() + Math.random(), text: line, loading: true }].slice(-6)
  );

  const stopApplyLoading = () =>
  setProcApplyLines((arr) => {
    if (!arr.length) return arr;
    const a = [...arr];
    const last = a[a.length - 1];
    a[a.length - 1] = { ...last, loading: false };
    return a;
  });

  const WorkflowTrail = ({ text = WORKFLOW_TEXT }) => (
  <div
    className="tf-crumbs"
    style={{
      fontWeight: 500,
      fontSize: 18,
      color: "#aeb4beff",        // grey
      margin: "2px 2px 10px",
    }}
  >
    {text}
  </div>
);


    // Suggest Tagging popup state
  const [procSuggestOpen, setProcSuggestOpen] = useState(false);
  const [procSuggestLines, setProcSuggestLines] = useState([]);
  const pushSuggest = (line) =>
    setProcSuggestLines((arr) =>
      [...arr, { id: Date.now() + Math.random(), text: line }].slice(-6)
    );

  // Console for Suggest Tagging
  const [logsSuggest, setLogsSuggest] = useState("");
  const [metrics, setMetrics] = useState(null);


  // Rollback popup state (NEW)
  const [procRollbackOpen, setProcRollbackOpen] = useState(false);
  const [procRollbackLines, setProcRollbackLines] = useState([]);
  const pushRollback = (line) =>
  setProcRollbackLines((arr) =>
    [...arr, { id: Date.now() + Math.random(), text: line }].slice(-6)
  );

// Rolling caption for rollback (NEW)
const [rbCaption, setRbCaption] = useState("Restoring backups and reverting files…");
useEffect(() => {
  if (!procRollbackOpen) return;
  const tips = [
    "Finding backups…",
    "Restoring original files…",
    "Cleaning temporary files…",
    "Verifying rollback…",
  ];
  let i = 0;
  const t = setInterval(() => setRbCaption(tips[(i++ % tips.length)]), 1100);
  return () => clearInterval(t);
}, [procRollbackOpen]);



const loadFigmaShot = async () => {
  try {
    // Cache-bust so we always fetch the latest generated image
    const res = await fetch(`${apiBase}/figma-image?t=${Date.now()}`, {
      method: "GET",
      cache: "no-store",
    });
    if (!res.ok) {
      setFigmaImgUrl("");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    setFigmaImgUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return url;
    });
  } catch {
    setFigmaImgUrl("");
  }
};


  // Inputs
  const [figmaUrl, setFigmaUrl] = useState(""
    // "https://www.figma.com/design/ZC6WcE8iXWma7RESnZdo65/Sample?node-id=37-2&p=f&t=PPAFTWzPI6hLZYSy-0"
  );
  // const [acLocalFile, setAcLocalFile] = useState(""
  //    "/home/aysingh/AI_Tagging_Sys/core/techSpecAgent/acceptance_criteria.txt"
  // );
  const [acLocalFile, setAcLocalFile] = useState("");
 // NEW: when user uses “Browse files…”, we store the file text here
  const [acText, setAcText] = useState("");
  const [acPickedName, setAcPickedName] = useState(""); // UI-only, show selected  filename
  // NEW: handle <input type="file"> and read text
  const onPickACFile = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setAcPickedName(f.name);
    try {
      const txt = await f.text();
      setAcText(txt);
    } catch (err) {
      console.error("Failed reading file:", err);
      setAcText("");
      alert("Could not read the selected file. Please try again or paste a server path.");
    }
  };


  
  // Default repo (can still be edited in the UI)
  // const REPO_DEFAULT = "/home/aysingh/TaggingUI";  // editable default
  // const [repoPath, setRepoPath] = useState("");
  // const getRepoPath = () => (repoPath || REPO_DEFAULT).trim();
  // Logs + previews
  const [logsRun, setLogsRun] = useState("");       // Step 2 (pipeline) terminal
  const [logsActions, setLogsActions] = useState(""); // Actions (step 4) terminal
  const [sheetRows, setSheetRows] = useState([]);
  const [mdText, setMdText] = useState("");
   // Diff modal state (Step 4 "View file differences")
  const [diffOpen, setDiffOpen] = useState(false);
  const [diffLoading, setDiffLoading] = useState(false);
  const [diffError, setDiffError] = useState("");
  const [diffPairs, setDiffPairs] = useState([]); // [{old:"/a/Help.js", new:"/a/Help.js.taggingai.bak"}]
  const [selectedDiff, setSelectedDiff] = useState(null); // index of selected pair
  const [procOpen, setProcOpen] = useState(false);
  const [procLines, setProcLines] = useState([]);
  // Results summary (derived from diffPairs)
  const [resCount, setResCount] = useState(0);
  const [resAdds, setResAdds] = useState(0);
  const [resDels, setResDels] = useState(0);
  const [resSummary, setResSummary] = useState("");
  // Which part of Actions we’re showing: "suggest" or "apply"
  const [actionsPhase, setActionsPhase] = useState("suggest");
  // Whether Suggest Tagging has finished (Implementation Guide ready)
  const [suggestDone, setSuggestDone] = useState(false);
  // Push a line into the processing ticker (keeps last 6, fades oldest)
  const pushProc = (line) =>
    setProcLines((arr) =>
      [...arr, { id: Date.now() + Math.random(), text: line }].slice(-6)
    );
// NEW: push a “loading” line (renders a tiny spinner next to it)
const pushProcLoading = (line) =>
  setProcLines((arr) =>
    [...arr, { id: Date.now() + Math.random(), text: line, loading: true }].slice(-6)
  );

const pushSuggestLoading = (line) =>
  setProcSuggestLines((arr) =>
    [...arr, { id: Date.now() + Math.random(), text: line, loading: true }].slice(-6)
  );

// NEW: stop loading on the most recent line (turns spinner off)
const stopProcLoading = () =>
  setProcLines((arr) => {
    if (!arr.length) return arr;
    const a = [...arr];
    const last = a[a.length - 1];
    a[a.length - 1] = { ...last, loading: false };
    return a;
  });
const stopSuggestLoading = () =>
  setProcSuggestLines((arr) => {
    if (!arr.length) return arr;
    const a = [...arr];
    const last = a[a.length - 1];
    a[a.length - 1] = { ...last, loading: false };
    return a;
  });

  // UI helpers
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const esRef = useRef(null);
  const scrollTo = (id) => {
   const el = document.getElementById(id);
   if (!el) return;
   const header = document.querySelector(".tf-header");
   const offset = header ? header.getBoundingClientRect().height + 8 : 0; // header height + small gap
   const y = el.getBoundingClientRect().top + window.pageYOffset - offset;
   window.scrollTo({ top: y, behavior: "smooth" });
   };
  useEffect(() => {
    if (showActionsOnly) {
      requestAnimationFrame(() =>
        scrollTo(actionsPhase === "apply" ? "apply" : "suggest")
      );
    }
  }, [showActionsOnly, actionsPhase]);


  const markDone = (k) => setDone((d) => ({ ...d, [k]: true }));

  // ---- pipeline runner ----
const runPipeline = async () => {
    const hasText = !!(acText && acText.trim());
    const hasPath = !!(acLocalFile && acLocalFile.trim());
    if (!figmaUrl || (!hasText && !hasPath)) {
      alert("Please enter Figma URL and provide Acceptance Criteria (file or server path).");
      return;
    }

  try {
    setProcOpen(true);
    setProcLines([]);
    setStep(1);
    scrollTo("step2");
    setLogsRun("");


    // 1) generate-techspec  (xlsx only)
    pushProcLoading("Generating TechSpec File");
    setLogsRun((s) => s + "▶ Generating TechSpec (xlsx)…\n");
    // Build request body safely: prefer ac_text (from Browse) else ac_local_file (manual path)
    const body = { figma_file_url: figmaUrl };
    if (hasText) body.ac_text = acText.trim();
    else if (hasPath) body.ac_local_file = acLocalFile.trim();

    const genRes = await fetch(`${apiBase}/generate-techspec`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!genRes.ok) {
      const err = await genRes.text();
      stopProcLoading();
      pushProc("❌ TechSpec generation failed");
      setLogsRun((s) => s + `❌ generate-techspec failed: ${err}\n`);
      return;
    }

    const gen = await genRes.json();
    stopProcLoading();
      pushProc("✅ TechSpec generated");
      setLogsRun((s) => s + `✅ TechSpec generated at: ${gen.output_path}\n`);

      // 2) preview ONLY the xlsx
    await sleep(500);
    pushProc("Loading TechSpec preview…", "📄");
    setLogsRun((s) => s + "▶ Loading TechSpec preview…\n");
    await loadTechspecPreview();
    pushProc("✅ Preview loaded", "✅");
    await sleep(400);
    // pushProc("Loading Figma screen…", "🖼️");
    await loadFigmaShot();
    // pushProc("✅ Figma screen loaded", "✅");
    setLogsRun((s) => s + "✅ Preview loaded\n");


    markDone(1);               // ✅ now Step 1 is complete; Next button will show
    setStep(1);                // stay on Step 1 until user clicks Next
    scrollTo("step3");         

    } catch (e) {
      pushProc("❌ Pipeline error", "⛔");
      setLogsRun((s) => s + `❌ Pipeline error: ${e.message}\n`);
    } finally {
      setTimeout(() => setProcOpen(false), 3000);
    }
  };
// Rotating captions to make popups feel alive
const [tsCaption, setTsCaption] = useState("We’re preparing your TechSpec and previews.");
const [sgCaption, setSgCaption] = useState("We’re preparing your suggestions.");
const [apCaption, setApCaption] = useState("Applying changes to your repo…");

useEffect(() => {
  if (!procOpen) return;
  const tips = ["Parsing Acceptance Criteria…", "Fetching Figma…", "Inferring columns…", "Formatting workbook…"];
  let i = 0;
  const t = setInterval(() => setTsCaption(tips[(i++ % tips.length)]), 1100);
  return () => clearInterval(t);
}, [procOpen]);

useEffect(() => {
  if (!procSuggestOpen) return;
  const tips = ["Scanning pages…", "Mapping components…", "Drafting rules…", "Polishing Results…"];
  let i = 0;
  const t = setInterval(() => setSgCaption(tips[(i++ % tips.length)]), 1100);
  return () => clearInterval(t);
}, [procSuggestOpen]);

useEffect(() => {
  if (!procApplyOpen) return;
  const tips = ["Creating backup files…", "Writing updates…", "Linting output…", "Finalizing…"];
  let i = 0;
  const t = setInterval(() => setApCaption(tips[(i++ % tips.length)]), 1100);
  return () => clearInterval(t);
}, [procApplyOpen]);


// REPLACE your loadDiffPairs with this version
const loadDiffPairs = async () => {
  try {
    setDiffLoading(true);
    setDiffError("");
    setDiffPairs([]);
    setSelectedDiff(null);

    const res = await fetch(`${apiBase}/view-difference`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      const txt = await res.text();
      setDiffError(`Could not load file differences (HTTP ${res.status}). ${txt || ""}`.trim());
      return;
    }

    const json = await res.json(); // { repo_root, items:[...] }
    const root = (json?.repo_root || "").replace(/\\/g, "/");
    setDiffRepoRoot(root);   // ← store it for the modal label
    const items = Array.isArray(json?.items) ? json.items : [];

    const normalize = (d) =>
      (Array.isArray(d) ? d.join("\n") : String(d || "")).replace(/\r\n/g, "\n");

    const pairs = items.map((it) => {
      const rel = (it.new || it.old || "").replace(root + "/", "");
      const raw = normalize(it.diff);
      const lines = raw.split("\n");

      let adds = 0, dels = 0;
      for (let ln of lines) {
        if (!ln) continue;
        if (ln.startsWith("+++") || ln.startsWith("---")) continue;
        if (ln.startsWith("\\ No newline at end of file")) continue;
        if (ln[0] === "+" && ln.slice(0,3) !== "+++") adds++;
        else if (ln[0] === "-" && ln.slice(0,3) !== "---") dels++;
      }

      // pass full blobs through if the API included them (no backend change required)
      const oldText = typeof it.old_text === "string" ? normalize(it.old_text) : null;
      const newText = typeof it.new_text === "string" ? normalize(it.new_text) : null;

      return { rel, old: it.old, new: it.new, adds, dels, unified: raw, oldText, newText };
    });

    setDiffPairs(pairs);
    if (pairs.length) setSelectedDiff(0);
     // --- Build Results summary ---
    const count = pairs.length;
    const adds  = pairs.reduce((s,p)=> s + (p.adds||0), 0);
    const dels  = pairs.reduce((s,p)=> s + (p.dels||0), 0);
    setResCount(count);
    setResAdds(adds);
    setResDels(dels);
    const names = pairs.map(p => p.rel || p.new || p.old).filter(Boolean);
    const listed = names.slice(0, 3).join(", ");
    const more = count > 3 ? "…" : "";
    setResSummary(
      count ? `File Changes: ${listed}${more}` : "No changes detected."
    );
  } catch (e) {
    setDiffError("Failed to load differences: " + (e?.message || e));
  } finally {
    setDiffLoading(false);
  }
};


const loadTechspecPreview = async () => {
  try {
    // 1) Cache-bust so we always fetch the newest XLSX after generation
    const res = await fetch(`${apiBase}/techspec-file?t=${Date.now()}`, {
      method: "GET",
      // ensure we don't reuse a cached connection in some setups
      cache: "no-store",
    });
    if (!res.ok) {
      setSheetRows([["Preview"], ["Unable to load techspec.xlsx (HTTP " + res.status + ")"]]);
      return;
    }

    // 2) Parse workbook from the binary
    const blob = await res.blob();
    const arrayBuf = await blob.arrayBuffer();
    const wb = XLSX.read(arrayBuf, { type: "array", cellDates: true });
    // 3) Choose the right sheet: prefer "TechSpec", then "Sheet1", else the first
    const preferredNames = ["TechSpec", "techspec", "Sheet1", "sheet1"];
    const foundName =
      preferredNames.find(n => wb.SheetNames.includes(n)) || wb.SheetNames[0];

    const sheet = wb.Sheets[foundName];
    if (!sheet) {
      setSheetRows([["Preview"], ["No sheets found in techspec.xlsx"]]);
      return;
    }

    // 4) Convert to a 2D array (rows of cells)
    const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, raw: false });

    // 5) Limit for UI; keep it snappy
    const MAX_ROWS = 30;
    const MAX_COLS = 25;
    const trimmed = rows
      .slice(0, MAX_ROWS)
      .map(r => (Array.isArray(r) ? r.slice(0, MAX_COLS) : [String(r ?? "")]));

    // 6) Fallback if empty
    if (trimmed.length === 0) {
      setSheetRows([["Preview"], ["techspec.xlsx appears to be empty"]]);
      return;
    }

    setSheetRows(trimmed);
  } catch (err) {
    setSheetRows([["Preview"], ["Error reading techspec.xlsx: " + (err?.message || err)]]);
  }
};




  const loadMarkdownPreview = async () => {
    // You also have /download/md; this one streams text for on-page preview
    const res = await fetch(`${apiBase}/tagging-markdown`);
    if (!res.ok) return;
    const text = await res.text();
    setMdText(text);
  };

  const applyTagging = async () => {
  try {
    setLogsActions(""); // fresh terminal


    // Go to Actions view and OPEN the "Applying…" popup
    setStep(4);
    setShowActionsOnly(true);
    setProcApplyOpen(true);
    setProcApplyLines([]);
    setApplyDone(false);
    pushApplyLoading("Preparing to apply tagging…", "🔁");

    // 1) suggestions (dynamic)
    setLogsActions((s) => s + "▶ Referring tagging suggestions…\n");

    const sugRes = await fetch(`${apiBase}/suggest-tagging`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // you can re-send { repo_url } the user typed earlier.
      body: JSON.stringify({ repo_url: repoUrl.trim() }),
    });
    if (!sugRes.ok) {
      const err = await sugRes.text();
      pushApplyLoading("❌ suggest-tagging failed");
      setLogsActions((s) => s + `❌ suggest-tagging failed: ${err}\n`);
      return;
    }
    stopApplyLoading();
    pushProc("✅ Tagging suggestions ready", "✅");
    setLogsActions((s) => s + "✅ Tagging suggestions ready\n");

    // 2) apply (dynamic — sends repo_path in body, matches backend)
    pushApplyLoading("Applying tagging to repo…", "🔧");
    setLogsActions((s) => s + "▶ Applying tagging to repo…\n");
    setLogsActions((s) => s + "   • Writing .bak backups to src/pages\n");
    setLogsActions((s) => s + "   • Updating matched files\n");

    const applyRes = await fetch(`${apiBase}/apply-tagging`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}), // ✅ no path needed; backend uses the stored repo root
    });
    if (!applyRes.ok) {
      const errText = await applyRes.text();
      pushApplyLoading("❌ apply-tagging failed", "⛔");
      setLogsActions((s) => s + `❌ apply-tagging failed: ${errText}\n`);
      return;
    }

    const j = await applyRes.json().catch(() => ({}));
    setApplyLogPath(j.log_path || "");
    stopApplyLoading();
    // pushProc("✅ Tagging applied", "✅");
    setProcApplyLines(arr =>
      [...arr, { id: Date.now() + Math.random(), text: "✅ Tagging applied", loading: false }].slice(-6)
    );                                      // <-- ADD

    setApCaption("Tagging applied");        // <-- Optional: change subtitle
    setApplyDone(true);                     
    setLogsActions(
      (s) =>
        s +
        `✅ Tagging applied. Log: ${j.log_path || "n/a"}\n` +
        "💡 Tip: click “View file differences” below to review changes.\n"
    );
    // Pull metrics written by backend (core/outputs/metrics.json via GET /metrics)
    try {
      const mr = await fetch(`${apiBase}/metrics`, { headers: { Accept: "application/json" } });
      if (mr.ok) setMetrics(await mr.json());
    } catch {}
    // ✅ Apply finished — show the same Apply UI inside the Results section
    markDone(3);
    markDone(4);
    setActionsPhase("apply");
    setShowActionsOnly(true);   // keep Actions area visible
    setStep(4);                 // highlight "4. Results"
    scrollTo("apply");          // Results = Apply view
    try { await loadDiffPairs(); } catch {}
  } catch (e) {
    pushApplyLoading("❌ Apply error", "⛔");
    setLogsActions((s) => s + `❌ Apply error: ${e.message}\n`);
  } finally {
    // close popup shortly after finish/error
    setTimeout(() => setProcApplyOpen(false), 6000);
  }
};

const suggestTagging = async () => {
  if (!repoUrl) {
    alert("Please enter a GitHub repo URL, e.g. https://github.com/owner/repo");
    return;
  }
  const isGitUrl = /^https?:\/\/(www\.)?github\.com\/[^\/]+\/[^\/]+(\/)?$/i.test(repoUrl.trim());
  if (!isGitUrl) {
    alert("Please provide a valid GitHub URL like https://github.com/owner/repo");
    return;
  }
  try {
    setLogsSuggest("");
    // Show popup
    setProcSuggestOpen(true);
    setProcSuggestLines([]);
    pushSuggestLoading("Preparing tagging suggestions…", "⚙️");
    pushSuggest("   • Reading TechSpec & repo structure");
    pushSuggest("   • Inferring component→tag rules");
    // Terminal:
    setLogsSuggest((s) => s + "▶ Preparing tagging suggestions…\n");
    setLogsSuggest((s) => s + "   • Reading TechSpec & repo structure\n");
    setLogsSuggest((s) => s + "   • Inferring component→tag rules\n");
    // Kick off suggestions (same input as Apply Tagging’s first step)

    const sugRes = await fetch(`${apiBase}/suggest-tagging`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: repoUrl.trim() }),   // ✅ send URL, backend clones it
    });

    if (!sugRes.ok) {
      const err = await sugRes.text();
      pushSuggest("❌ suggest-tagging failed", "⛔");
      setLogsSuggest((s) => s + `❌ suggest-tagging failed: ${err}\n`);
      return;
    }
    const payload = await sugRes.json().catch(()=> ({}));
    stopSuggestLoading();
    pushSuggest("✅ Suggestions ready", "✅");
    if (payload?.repo_path_used) {
   setResolvedRepoPath(payload.repo_path_used); // ✅ show local path separately
    }
    setLogsSuggest((s) => s + "✅ Suggestions ready\n");
    // Load freshly written Implementation Guide
    pushSuggest("Loading Implementation Guide preview…", "📘");
    await loadMarkdownPreview();
    pushSuggest("✅ Implementation Guide loaded", "✅");
    setSuggestDone(true);
    markDone(2);       // ✅ Suggest step completed
    setStep(2);        // keep pills honest
  } catch (e) {
    pushSuggest("❌ Suggest error", "⛔");
    setLogsSuggest((s) => s + `❌ Suggest error: ${e.message}\n`);
  } finally {
    setTimeout(() => setProcSuggestOpen(false), 3000);
  }
};


// openSideBySide (renders GitHub-style + real "whole file" toggle)
const openSideBySide = (pair) => {
  const esc = (s="") => String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  const norm = (t) => String(t ?? "").replace(/\r\n/g, "\n");

  // Parse unified diff (for side-by-side hunks)
  const raw = norm(Array.isArray(pair.unified) ? pair.unified.join("\n") : pair.unified);
  const lines = raw.split("\n");
  const HUNK = /@@\s+-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@/;

  let lno = 0, rno = 0, addCount = 0, delCount = 0;
  const rows = [];
  for (let ln of lines) {
    if (!ln) continue;
    if (ln.startsWith("+++ ") || ln.startsWith("--- ")) continue;
    if (ln.startsWith("\\ No newline at end of file")) continue;
    const m = ln.match(HUNK);
    if (m) { lno = +m[1]; rno = +m[2]; rows.push({ t:"gap" }); continue; }
    const tag = ln[0], body = ln.slice(1);
    if (tag === "+") { rows.push({ t:"add", lno:"", rno, left:"", right:body }); rno++; addCount++; }
    else if (tag === "-") { rows.push({ t:"del", lno, rno:"", left:body, right:"" }); lno++; delCount++; }
    else if (tag === " ") { rows.push({ t:"ctx", lno, rno, left:body, right:body }); lno++; rno++; }
  }

  // Prefer full blobs if present
  const fullLeft  = typeof pair.oldText === "string" ? pair.oldText.split("\n") : null;
  const fullRight = typeof pair.newText === "string" ? pair.newText.split("\n") : null;

  const page = `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Diff • ${esc(pair.rel || pair.old || "")}</title>
<style>
  :root{--bg:#fff;--text:#24292e;--muted:#57606a;--grid:#d0d7de;--add:#e6ffed;--add-b:#34d058;--del:#ffeef0;--del-b:#d73a49;--hunk:#f6f8fa}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);font:13px/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}
  .wrap{padding:16px;overflow:auto}
  header{display:flex;gap:12px;align-items:center;margin-bottom:8px}
  header h1{margin:0;font:600 14px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
  .legend{color:var(--muted);font:12px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
  .badge{padding:3px 8px;border-radius:999px;color:#fff;background:#2da44e;font:12px/1 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
  .badge.del{background:#cf222e}
  .toolbar{display:flex;gap:8px;align-items:center;margin:8px 0}
  .btn{border:1px solid var(--grid);background:#fff;border-radius:6px;padding:6px 10px;cursor:pointer}
  .btn[aria-pressed="true"]{background:#24292e;color:#fff}
  .filehdr{border:1px solid var(--grid);border-bottom:0;background:var(--hunk);padding:8px 10px;border-radius:6px 6px 0 0;font:600 12px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
  .table{border:1px solid var(--grid);width:100%;border-collapse:collapse;table-layout:fixed}
  .table th,.table td{border:1px solid var(--grid);padding:3px 6px;vertical-align:top}
  .table thead th{position:sticky;top:0;background:#fff;z-index:2}
  .gutter{width:52px;color:#8c959f;text-align:right;background:#fff}
  .code{white-space:pre;overflow:auto}
  .wraplines .code{white-space:pre-wrap;word-break:break-word}
  tr.add td{background:var(--add);border-color:var(--add-b)}
  tr.del td{background:var(--del);border-color:var(--del-b)}
  tr.gap td{background:var(--hunk);color:#57606a}
  .twocol{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  .note{color:#b45309;background:#fffbeb;border:1px solid #f59e0b;padding:6px 8px;border-radius:6px;font:12px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
</style></head>
<body>
<div class="wrap">
  <header>
    <h1>Side-by-side diff</h1><span class="legend">Green = additions, Red = deletions</span>
    <span style="margin-left:auto" class="badge">+ ${addCount}</span><span class="badge del">- ${delCount}</span>
  </header>

  <div class="toolbar">
    <button id="wrapBtn" class="btn" aria-pressed="true">Wrap lines</button>
    <button id="toggleBtn" class="btn" data-mode="hunks">Show whole file</button>
  </div>

  <div class="filehdr">${esc(pair.rel || pair.old || "")}</div>
  <div id="mount"></div>
</div>

<script>
  const rows=${JSON.stringify(rows)};
  const fullL=${JSON.stringify(fullLeft)};
  const fullR=${JSON.stringify(fullRight)};

  const mount=document.getElementById('mount');
  const wrapBtn=document.getElementById('wrapBtn');
  const toggleBtn=document.getElementById('toggleBtn');

  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

  function renderHunks(){
    mount.innerHTML=\`
      <table id="tab" class="table wraplines">
        <thead><tr><th class="gutter">#</th><th>Original (.bak)</th><th class="gutter">#</th><th>Updated</th></tr></thead>
        <tbody>\${rows.map(r=>{
          if(r.t==='gap') return '<tr class="gap"><td colspan="4">…</td></tr>';
          const cls=r.t==='add'?'add':(r.t==='del'?'del':'');
          return \`<tr class="\${cls}">
            <td class="gutter">\${r.lno===""?"":r.lno+1}</td><td class="code">\${esc(r.left??"")}</td>
            <td class="gutter">\${r.rno===""?"":r.rno+1}</td><td class="code">\${esc(r.right??"")}</td>
          </tr>\`;
        }).join('')}</tbody>
      </table>\`;
    toggleBtn.textContent="Show whole file";
    toggleBtn.dataset.mode="hunks";
  }

  function renderWhole(){
    // If API gave us blobs, use them. Otherwise stitch the diff (with gap markers).
    let leftLines = fullL || [];
    let rightLines = fullR || [];
    if (!leftLines.length || !rightLines.length){
      // best-effort from diff
      leftLines = []; rightLines = [];
      for(const r of rows){
        if(r.t==='gap'){ leftLines.push('…'); rightLines.push('…'); continue; }
        leftLines.push(r.left ?? "");
        rightLines.push(r.right ?? "");
      }
    }

    const leftHTML = leftLines.map((t,i)=>\`<tr><td class="gutter">\${i+1}</td><td class="code">\${esc(t)}</td></tr>\`).join("");
    const rightHTML= rightLines.map((t,i)=>\`<tr><td class="gutter">\${i+1}</td><td class="code">\${esc(t)}</td></tr>\`).join("");

    mount.innerHTML=\`
      <div class="twocol">
        <div>
          <table id="tabL" class="table wraplines">
            <thead><tr><th class="gutter">#</th><th>Original (.bak)</th></tr></thead>
            <tbody>\${leftHTML}</tbody>
          </table>
        </div>
        <div>
          <table id="tabR" class="table wraplines">
            <thead><tr><th class="gutter">#</th><th>Updated</th></tr></thead>
            <tbody>\${rightHTML}</tbody>
          </table>
        </div>
      </div>
      \${(!fullL || !fullR)}\`;
    toggleBtn.textContent="Show Updated Part";
    toggleBtn.dataset.mode="whole";
  }

  function toggle(){
    const mode = toggleBtn.dataset.mode;
    if(mode==="hunks") renderWhole(); else renderHunks();
  }

  function setWrap(){
    document.querySelectorAll('table').forEach(t=>{
      const wrapped = t.classList.toggle('wraplines');
      wrapBtn.setAttribute('aria-pressed', wrapped ? 'true':'false');
    });
  }

  wrapBtn.addEventListener('click', setWrap);
  toggleBtn.addEventListener('click', toggle);

  // initial render
  renderHunks();
</script>
  </body></html>`;

    const blob = new Blob([page], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.target = "_blank"; a.rel = "noopener";
    document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 3000);
  };




const rollbackChanges = async () => {
  // show popup immediately (even if validation fails) and keep it on at least 5s
  const start = Date.now();
  setProcRollbackOpen(true);
  setProcRollbackLines([]);
  pushRollback("Preparing rollback…");
  await sleep(600); // let the first line breathe
  try {
    // const path = (repoPath || "").trim();
    // if (!path) {
    //   pushRollback("❌ Repo path required.");
    //   setLogsActions((s) => s + "❌ Repo path required for rollback.\n");
    //   throw new Error("Repo path required");
    // }

    setLogsActions((s) => s + "▶ Rolling back changes…\n");
    pushRollback("Restoring files from .bak backups…");
    await sleep(900); // stage the second line so it feels live


    const res = await fetch(`${apiBase}/rollback-changes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ delete_backups: true }),  // ✅ also delete .bak files
    });

    if (!res.ok) {
      const errText = await res.text();
      pushRollback("❌ Rollback failed");
      setLogsActions((s) => s + `❌ rollback failed: ${errText}\n`);
      return;
    }

    pushRollback("Deleting backup files…");
    await sleep(500);
    await sleep(500); // brief pause before success
    pushRollback("✅ Rollback complete");
    setLogsActions((s) => s + "✅ Rollback complete\n");
    markDone(4);
  } catch (e) {
    pushRollback("❌ Rollback error");
    setLogsActions((s) => s + `❌ Rollback error: ${e.message}\n`);
  } finally {
    const elapsed = Date.now() - start;
    const remain = Math.max(0, 5000 - elapsed); // ⏱️ ensure at least 5s visible
    setTimeout(() => setProcRollbackOpen(false), remain);
  }
};




  // ----- presentational bits (same look & feel you had) -----
  const Pill = ({ label, active, done, disabled, onClick }) => (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      title={disabled ? "Complete this step to enable" : ""}
      className={`tf-pill ${active ? "tf-pill--active" : ""} ${done ? "tf-pill--done" : ""} ${disabled ? "tf-pill--disabled" : ""}`}
    >
      {label}
    </button>
  );
  const Connector = ({ lit }) => <div className={`tf-connector ${lit ? "tf-connector--lit" : ""}`} />;
  const Card = ({ title, children, right }) => (
    <div className="tf-card">
      <div className="tf-card__hdr">
        <h3 className="tf-card__title">{title}</h3>
        {right}
      </div>
      {children}
    </div>
  );

  return (
    <div className="tf-wrap">
      <div className="tf-container">
        {/* Header */}
        <div className="tf-header">
          <div className="tf-brand">
            <img className="tf-logo" src="/ICS.png" alt="Logo" width={48} height={48} style={{ objectFit: "contain", borderRadius: 5 }}/>
            <div className="tf-brand-text">
              <div className="tf-title">Tagging AI</div>
              <div className="tf-subtitle">Generate | Suggest | Apply</div>
            </div>
          </div>
          <div className="tf-steps">
  {/* 1. TechSpec */}
  <Pill
    label="1. TechSpec Generation"
    active={step === 1}
    done={done[1]}
    disabled={false}
    onClick={() => { setShowActionsOnly(false); setStep(1); scrollTo("step1"); }}
  />
  <Connector lit={done[1]} />

  {/* 2. Suggest Tagging */}
<Pill
  label="2. Suggest Tagging"
  active={step === 2}
  done={done[2]}
  disabled={!done[1]}
  onClick={() => {
    setActionsPhase("suggest");
    setShowActionsOnly(true);
    setStep(2);
    scrollTo("suggest");
  }}
/>
  <Connector lit={done[2]} />

  {/* 3. Apply Tagging */}
<Pill
  label="3. Apply Tagging"
  active={step === 3}
  done={done[3]}
  disabled={!done[2]}
  onClick={() => {
    setActionsPhase("apply");
    setShowActionsOnly(true);
    setStep(3);
    scrollTo("apply");
  }}
/>
  <Connector lit={done[3]} />

  {/* 4. Results (final) */}
  <Pill
    label="4. Results"
    active={step === 4}
    done={done[4]}
    disabled={!done[3]}
    onClick={() => {
     setActionsPhase("apply");     // show Apply tab
     setShowActionsOnly(true);     // render Actions area
     setStep(4);                   // highlight Results pill
     markDone(4);
     scrollTo("apply");            // jump to Apply section
   }}
  />
</div>

        </div>

  {/* Step 1 — Inputs */}
  {!showActionsOnly && (
    <>
      {/* Step 1 — Inputs */}
      <section id="step1" className="tf-section">
        <WorkflowTrail />
        <Card
          title="Step 1 — TechSpec Generation"
          right={<div className="tf-meta">Figma • AC file</div>}
        >
          <div className="tf-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6 }}>
                Figma File URL
              </div>
              <input
                className="tf-input"
                placeholder="https://www.figma.com/..."
                value={figmaUrl}
                style={{width:'500px'}}
                onChange={(e) => setFigmaUrl(e.target.value)}
              />
            </div>

            <div>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6 }}>
                Acceptance Criteria (pick a file or paste a server path)
              </div>

              {/* Browse files — reads content into acText (preferred) */}
              <div className="tf-row" style={{ gap: 8, alignItems: "center", marginBottom: 8 }}>
                <label className="tf-btn tf-btn--chip" style={{ cursor: "pointer" }}>
                  Browse files…
                  <input type="file" accept=".txt,.md,.csv,.json"
                         onChange={onPickACFile}
                         style={{ display: "none" }} />
                </label>
                 <input
   className="tf-input"
   style={{ width: 260 }}
   readOnly
   placeholder="No file selected"
   value={acPickedName}
   title={acPickedName || "No file selected"}
 />
              </div>

              {/* Optional: manual path (fallback when server can read local paths)
              <input
                className="tf-input"
                placeholder="/path/to/acceptance_criteria.txt"
                value={acLocalFile}
                style={{ width: '500px' }}
                onChange={(e) => setAcLocalFile(e.target.value)}
              />
              <div className="tf-caption">
                Tip: If you use <b>Browse files…</b>, we’ll use the file’s content directly.
                If you paste a path, it must be readable on the API host.
              </div> */}
            </div>

          </div>

          <div className="tf-row">
            <button className="tf-btn tf-btn--primaryy" onClick={runPipeline}>
              Generate TechSpec
            </button>
            <span className="tf-caption">Backend: {apiBase}</span>
          </div>
        </Card>
      </section>

      <section id="step3" className="tf-section">
  <div className="tf-col2">
    <Card
      title="Tech Spec (techspec.xlsx)"
      right={
        <div className="tf-row tf-gap">
          <button className="tf-btn tf-btn--chip" onClick={loadTechspecPreview}>
            Reload Preview
          </button>
          <a className="tf-download-pill" href={`${apiBase}/techspec-file?t=${Date.now()}`}>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3v10.17l3.59-3.58L17 11l-5 5-5-5 1.41-1.41L11 13.17V3h1zM5 18h14v2H5z"/>
            </svg>
            Download TechSpec.xlsx
          </a>
        </div>
      }
    >
      <div className="tf-tablewrap tf-tablewrap--wide">
        <table className="tf-table tf-table--fixed">
          <tbody>
            {sheetRows.length === 0 && (
              <tr><td className="tf-empty">No preview loaded yet.</td></tr>
            )}
            {sheetRows.map((row, i) => (
              <tr key={i} className={i === 0 ? "tf-tr--head tf-tr--sticky" : ""}>
                {row.map((cell, j) => (
                  <td key={j} className="tf-td tf-td--wrap">{String(cell ?? "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
    {/* RIGHT: Figma image */}
<Card
  title="Figma Screen (latest run)"
  right={
    <div className="tf-row tf-gap">
      <button className="tf-btn tf-btn--chip" onClick={loadFigmaShot}>
        Reload Image
      </button>
      <a className="tf-download-pill" href={`${apiBase}/figma-image?t=${Date.now()}`}>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 3v10.17l3.59-3.58L17 11l-5 5-5-5 1.41-1.41L11 13.17V3h1zM5 18h14v2H5z"/>
        </svg>
        Download figma_screen.png
      </a>
    </div>
  }
>
  <div className="tf-imgwrap">
    {figmaImgUrl ? (
      <img
        src={figmaImgUrl}
        alt="Figma screen"
        style={{ width: "100%", height: "auto", borderRadius: 8, display: "block" }}
      />
    ) : (
      <div className="tf-empty">No image available yet.</div>
    )}
  </div>
</Card>

  </div>

  {done[1] && (  // show Next after TechSpec is done
  <div className="tf-row" style={{ justifyContent: "flex-end" }}>
    <button
      className="tf-btn tf-btn--primary"
      onClick={() => {
        setActionsPhase("suggest");
        setShowActionsOnly(true);
        setStep(2);
        scrollTo("suggest");
      }}
    >
      Next →
    </button>
  </div>
)}

</section>


      {/* Live logs */}
      <section id="step2" className="tf-section">
        <Card title="Run output" right={<button className="tf-btn tf-btn--chip" onClick={()=>{if(esRef.current){esRef.current.close();esRef.current=null;}}}>Stop</button>}>
          <pre className="tf-log">{logsRun || "Waiting…"}</pre>
          {/* <div className="tf-row">
            <button className="tf-btn tf-btn--blue" onClick={()=>{setStep(3);scrollTo("step3");}}>Continue to Results</button>
          </div> */}
        </Card>
      </section>
    </>
  )}

    {/* ✅ Actions area: only visible after Next */}
    {showActionsOnly && (
      <>
      {actionsPhase === "suggest" && (
  <section id="suggest" className="tf-section">
     <WorkflowTrail />
    <Card>
      <div className="tf-row" style={{ alignItems: "flex-end", flexWrap: "wrap", gap: 12 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10}}>Step 2 - Suggest Tagging</div>
          <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 6 }}>GitHub Repo URL</div>
          <input
            className="tf-input"
            placeholder="https://github.com/repo"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
          />
        </div>
        <button className="tf-btn tf-btn--green" onClick={suggestTagging}>
          Suggest Tagging
        </button>
      </div>
    </Card>
        <br/>
    {/* Implementation Guide lives under Suggest Tagging */}
    <Card
      title="Implementation Guide (tagging_unified.md)"
      right={
        <div className="tf-row tf-gap">
          <button className="tf-btn tf-btn--chip" onClick={loadMarkdownPreview}>Reload Preview</button>
          <a className="tf-download-pill" href={`${apiBase}/tagging-markdown`}>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3v10.17l3.59-3.58L17 11l-5 5-5-5 1.41-1.41L11 13.17V3h1zM5 18h14v2H5z"/>
            </svg>
            Download tagging_unified.md
          </a>
        </div>
      }
    >
      <div className="tf-preview-box">
        {mdText ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              table: (p) => <table className="tf-table" {...p} />,
              thead: (p) => <thead className="tf-thead" {...p} />,
              th: (p) => <th className="tf-th" {...p} />,
              td: (p) => <td className="tf-td tf-td--wrap" {...p} />,
              code: ({ inline, children, ...p }) =>
                inline ? <code className="tf-code-inline" {...p}>{children}</code>
                       : <pre className="tf-code-block"><code {...p}>{children}</code></pre>,
              h1: (p) => <h3 {...p} />,
              h2: (p) => <h4 {...p} />,
              h3: (p) => <h5 {...p} />,
            }}
          >
            {mdText}
          </ReactMarkdown>
        ) : (
          <div className="tf-empty">No markdown loaded yet.</div>
        )}
      </div>
      {/* IG footer controls */}
<div className="tf-row" style={{ justifyContent: "space-between", marginTop: 12 }}>
  <button
    className="tf-btn tf-btn--primary"   // same style as Next
    onClick={() => { setShowActionsOnly(false); setStep(1); scrollTo("step1"); }}
  >
    ← Back
  </button>

  <button
    className="tf-btn tf-btn--primary"
    disabled={!(suggestDone && mdText)}
    onClick={() => {
    setActionsPhase("apply");
    setShowActionsOnly(true);
    setStep(3);              // ✅ highlight Apply Tagging pill
    scrollTo("apply");
  }}
    title={suggestDone && mdText ? "" : "Generate suggestions to continue"}
  >
    Next →
  </button>
</div>

    </Card>
<br/>
    {/* Console */}
    <Card title="Suggest Tagging — output">
      <pre className="tf-log">{logsSuggest || "Waiting…"}</pre>
    </Card>


    {/* Next → to go to Apply Tagging once is ready */}
    {suggestDone && mdText && (
<button onClick={() => {
    setActionsPhase("apply");
    setShowActionsOnly(true);
    setStep(3);              // ✅ highlight Apply Tagging pill
    scrollTo("apply");
  }}>
    Next →
  </button>
)}
  </section>
)}

{actionsPhase === "apply" && (
  <>
    <section id="apply" className="tf-section">
       <WorkflowTrail />
      <Card
        title="Step 3 — Apply Tagging"
        right={
          <div className="tf-row" style={{ justifyContent: "space-between", marginTop: 12 }}>
  <button
    className="tf-btn tf-btn--primary"
    onClick={() => {
   setActionsPhase("suggest");
   setShowActionsOnly(true);
   setStep(2);               // ✅ highlight Suggest Tagging pill
   scrollTo("suggest");
 }}
  >
    ← Back
  </button>
</div>
        }
      >
        <div className="tf-row" style={{ alignItems: "flex-end", flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6 }}>Repo (selected in Suggest Tagging)</div>
            <input
              className="tf-input"
              placeholder="Using the cloned repo from Suggest Tagging"
              value={resolvedRepoPath || ""}
              readOnly
            />
          </div>
          <button className="tf-btn tf-btn--green" onClick={applyTagging}>
            Apply Tagging
          </button>
        </div>
      </Card>
    </section>

    <div className="tf-row" style={{ justifyContent: "start" }}>
      <button
        className="tf-btn tf-btn--blue"
        onClick={async () => {
          await loadDiffPairs();                     // ✅ asks backend for current repo
          setDiffOpen(true);
        }}
      >
        View file differences
      </button>
    </div>

    {/* --- Results (summary) --- */}
    <section className="tf-section">
      <Card
        title="Results"
        right={
          <div className="tf-row tf-gap">
            <span className="tf-badge">{resCount} file{resCount===1?"":"s"} updated</span>
          </div>
        }
      >
        {resCount === 0 ? (
          <div className="tf-empty">No changes detected yet.</div>
        ) : (
          <div>
            <p className="tf-summary" style={{ marginBottom: 6 }}>{resSummary}</p>
                {metrics && (
      <div className="tf-row tf-gap" style={{ margin: "6px 0 10px" }}>
        <span className="tf-chip tf-chip--ok">items processed: <b>{metrics.items_processed ?? 0}</b></span>
        <span className="tf-chip tf-chip--warn">failed: <b>{metrics.failed ?? 0}</b></span>
        <span className="tf-chip">files modified: <b>{metrics.files_modified ?? 0}</b></span>
        <span className="tf-chip">backups created: <b>{metrics.backups_created ?? 0}</b></span>
      </div>
    )}
            <div className="tf-muted">
              ✅ Tagging applied. Log: {applyLogPath || "n/a"}
            </div>
          </div>
        )}
      </Card>
    </section>

    <section className="tf-section">
      <Card
        title="Rollback (if needed)"
        right={<button className="tf-btn tf-btn--danger" onClick={rollbackChanges}>Rollback Changes</button>}
      >
        <div className="tf-empty">Use rollback after verifying changes in your repo.</div>
      </Card>
    </section>

    <section id="action-logs" className="tf-section">
      <Card
        title="Run output"
        right={
          <button className="tf-btn tf-btn--chip" onClick={() => { if (esRef.current) { esRef.current.close(); esRef.current = null; } }}>
            Stop
          </button>
        }
      >
        <pre className="tf-log">{logsActions || "Waiting…"}</pre>
      </Card>
    </section>
  </>
)}
      </>  
    )}
    {/* === Processing Popup (Generating TechSpec) === */}
{procOpen && (
  <div className="tf-modal">
    <div className="tf-modal__backdrop"></div>
    <div className="tf-modal__card" style={{ maxWidth: 520, textAlign: "center" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
        {/* HEADER — replace both pieces */}
<div
  style={{
    width: 44, height: 44, borderRadius: "50%",
    display: "grid", placeItems: "center",
    boxShadow: "inset 0 0 0 3px #e5e7eb",
    animation: "tfPulse 1200ms ease-in-out infinite",
  }}
>
  <span style={{ fontSize: 20 }}>📊</span>   {/* 6) emoji loader */}
</div>

<h3 className="tf-modal__title" style={{ marginTop: 4 }}>Processing…</h3>
<div className="tf-muted">{tsCaption}</div>   {/* 5) rotating subtitle */}
      </div>

      {/* rolling/fading log lines */}
<div style={{ marginTop: 14 }}>
  
</div>
{procLines.map((l, idx, arr) => (
    <div
      key={l.id}
      style={{
        display: "flex",
        gap: 8,
        alignItems: "center",
        opacity: (idx + 1) / arr.length,
        transform: `translateY(${(arr.length - idx - 1) * 1.5}px)`,
        transition: "opacity 320ms ease, transform 320ms ease",
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        fontSize: 13,
        color: "#111827",
        whiteSpace: "pre-wrap",
      }}
    >
         {l.loading && (
     <span
       aria-hidden
       style={{
         width: 12,
         height: 12,
         borderRadius: "50%",
         border: "2px solid #e5e7eb",
         borderTopColor: "#111827",
         display: "inline-block",
         animation: "tfSpin 900ms linear infinite",
       }}
     />
   )}
   <span>{l.text}</span>

    </div>
  ))}
    </div>
  </div>
)}

{/* === Processing Popup (Suggest Tagging) — same format as TechSpec === */}
{procSuggestOpen && (
  <div className="tf-modal">
    <div className="tf-modal__backdrop"></div>
    <div className="tf-modal__card" style={{ maxWidth: 520, textAlign: "center" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
        {/* HEADER — replace both pieces */}
<div
  style={{
    width: 44, height: 44, borderRadius: "50%",
    display: "grid", placeItems: "center",
    boxShadow: "inset 0 0 0 3px #e5e7eb",
    animation: "tfPulse 1200ms ease-in-out infinite",
  }}
>
  <span style={{ fontSize: 20 }}>🧠</span>   {/* 6) emoji loader */}
</div>

<h3 className="tf-modal__title" style={{ marginTop: 4 }}>Processing…</h3>
<div className="tf-muted">{sgCaption}</div>   {/* 5) rotating subtitle */}

      </div>

      {/* rolling/fading log lines (same behavior) */}
      <div style={{ marginTop: 14 }}>
        {procSuggestLines.map((l, idx, arr) => (
  <div
    key={l.id}
    style={{
      display: "flex",
      gap: 8,
      alignItems: "center",
      opacity: (idx + 1) / arr.length,
      transition: "opacity 240ms ease",
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
      fontSize: 13,
      color: "#111827",
    }}
  >
    {l.loading && (
      <span
        aria-hidden
        style={{
          width: 12,
          height: 12,
          borderRadius: "50%",
          border: "2px solid #e5e7eb",
          borderTopColor: "#111827",
          display: "inline-block",
          animation: "tfSpin 900ms linear infinite",
        }}
      />
    )}
    <span>{l.text}</span>
  </div>
))}

      </div>
    </div>
  </div>
)}

{/* === Processing Popup (Applying Tagging) === */}
{procApplyOpen && (
  <div className="tf-modal">
    <div className="tf-modal__backdrop"></div>
    <div className="tf-modal__card" style={{ maxWidth: 520, textAlign: "center" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
        {/* HEADER — replace/add both pieces */}
{/* HEADER — loader until applyDone, then static check */}
{!applyDone ? (
  <div
    style={{
      width: 44, height: 44, borderRadius: "50%",
      display: "grid", placeItems: "center",
      boxShadow: "inset 0 0 0 3px #e5e7eb",
      animation: "tfPulse 1200ms ease-in-out infinite",
    }}
  >
    <span style={{ fontSize: 20 }}>🛠️</span>
  </div>
) : (
  <div
    style={{
      width: 44, height: 44, borderRadius: "50%",
      display: "grid", placeItems: "center",
      boxShadow: "inset 0 0 0 3px #e5e7eb",
    }}
  >
    <span style={{ fontSize: 20 }}>✅</span>
  </div>
)}

<h3 className="tf-modal__title" style={{ marginTop: 4 }}>
  {applyDone ? "Done" : "Applying tagging…"}
</h3>
<div className="tf-muted">{apCaption}</div>


  {/* 5) rotating subtitle */}
      </div>

      {/* rolling/fading backend log lines */}
      <div style={{ marginTop: 14 }}>
        {procApplyLines.map((l, idx) => (
  <div
    key={l.id}
    style={{
      display: "flex",
      gap: 8,
      alignItems: "center",
      opacity: (idx + 1) / procApplyLines.length,
      transition: "opacity 240ms ease",
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
      fontSize: 13,
      color: "#111827",
    }}
  >
    {l.loading && (
      <span
        aria-hidden
        style={{
          width: 12,
          height: 12,
          borderRadius: "50%",
          border: "2px solid #e5e7eb",
          borderTopColor: "#111827",
          display: "inline-block",
          animation: "tfSpin 900ms linear infinite",
        }}
      />
    )}
    <span>{l.text}</span>
  </div>
))}
      </div>
    </div>
  </div>
)}

{/* === Processing Popup (Rollback Changes) — same format === */}
{procRollbackOpen && (
  <div className="tf-modal">
    <div className="tf-modal__backdrop"></div>
    <div className="tf-modal__card" style={{ maxWidth: 520, textAlign: "center" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
        <div
          style={{
            width: 44, height: 44, borderRadius: "50%",
            display: "grid", placeItems: "center",
            boxShadow: "inset 0 0 0 3px #e5e7eb",
            animation: "tfPulse 1200ms ease-in-out infinite",
          }}
        >
          <span style={{ fontSize: 20 }}>↩️</span>
        </div>

        <h3 className="tf-modal__title" style={{ marginTop: 4 }}>Rolling back changes…</h3>
<div className="tf-muted">{rbCaption}</div>
      </div>

      {/* rolling/fading lines */}
      <div style={{ marginTop: 14 }}>
        {procRollbackLines.map((l, idx, arr) => (
          <div
            key={l.id}
            style={{
              display: "flex", gap: 8, alignItems: "center",
              opacity: (idx + 1) / arr.length,
              transform: `translateY(${(arr.length - idx - 1) * 1.5}px)`,
              transition: "opacity 320ms ease, transform 320ms ease",
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              fontSize: 13, color: "#111827", whiteSpace: "pre-wrap",
            }}
          >
            <span>{l.text}</span>
          </div>
        ))}
      </div>
    </div>
  </div>
)}


{/* === Diff Modal === */}
{diffOpen && (
  <div className="tf-modal">
    <div
      className="tf-modal__backdrop"
      onClick={() => setDiffOpen(false)}
    ></div>

    <div className="tf-modal__card">
      <div className="tf-modal__hdr">
        <h3 className="tf-modal__title">Changes summary</h3>
        <button
          className="tf-btn tf-btn--chip"
          onClick={() => setDiffOpen(false)}
        >
          Close
        </button>
      </div>

      {diffLoading ? (
        <div className="tf-empty">Scanning repo…</div>
      ) : diffError ? (
        <div className="tf-error">{diffError}</div>
      ) : (
        <>
          <div className="tf-muted" style={{ marginBottom: 8 }}>
  Folder: <code>{diffRepoRoot || resolvedRepoPath || "unknown"}</code>
</div>

          {diffPairs.length === 0 ? (
            <div className="tf-empty">No updated files found (.bak).</div>
          ) : (
            <div className="tf-changes">
              <div className="tf-changes__meta">
                {diffPairs.length} file{diffPairs.length > 1 ? "s" : ""} changed
                <span className="tf-changes__legend">
                  Green = additions, Red = deletions
                </span>
              </div>

              <ul className="tf-changes__list">
                {diffPairs.map((p, i) => {
                  const total = Math.max(1, (p.adds || 0) + (p.dels || 0));
                  const addPct = Math.round(((p.adds || 0) / total) * 100);
                  const delPct = 100 - addPct;

                  return (
                    <li
                      key={i}
                      className={`tf-changes__item ${
                        selectedDiff === i ? "is-selected" : ""
                      }`}
                      onClick={() => setSelectedDiff(i)}
                      title="Open side-by-side diff"
                    >
                      <div className="tf-changes__file">
                        <span className="tf-file-ico" aria-hidden>
                          📄
                        </span>
                        <span className="tf-file-path">{p.rel || p.old}</span>
                        <span className="tf-adddel">
                          <span
                            className="tf-adds"
                            style={{ width: `${addPct}%` }}
                          ></span>
                          <span
                            className="tf-dels"
                            style={{ width: `${delPct}%` }}
                          ></span>
                        </span>
                      </div>

                      <div className="tf-changes__counts">
                        <span className="tf-add">+{p.adds || 0}</span>
                        <span className="tf-del">-{p.dels || 0}</span>
                      </div>
                    </li>
                  );
                })}
              </ul>

              <div className="tf-modal__footer">
               <button
  className="tf-btn tf-btn--blue"
  disabled={selectedDiff === null}
  onClick={() => {
    const idx = selectedDiff ?? 0;
    openSideBySide(diffPairs[idx]);   // ← open polished new tab from JSON data
  }}
>
  View File
</button>
                {/* (Optional) unified diff button could go here */}

                {/* <button
                  className="tf-btn tf-btn--chip"
                  onClick={() => setDiffOpen(false)}
                >
                  CLOSE
                </button> */}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  </div>
)}
        <div className="tf-footer">TestFlow • API-connected</div>
      </div>
    </div>
  );
}