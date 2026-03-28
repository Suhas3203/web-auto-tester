"""
FastAPI web service for Web Auto Tester.

Provides a web UI and REST API to run automated tests against any deployed
web application. Test history is persisted in a database (SQLite locally,
PostgreSQL on Render via Neon/Supabase).
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import re
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel

from web_auto_tester.runner import AutoTestRunner
from web_auto_tester.database import init_db, save_run, list_runs, get_run


# ── App lifespan: init DB on startup ─────────────────────────────────────────
_main_loop: asyncio.AbstractEventLoop | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _main_loop
    _main_loop = asyncio.get_running_loop()
    await init_db()
    yield


def _save_run_threadsafe(**kwargs) -> None:
    """Call save_run() from a background thread onto the main event loop."""
    if _main_loop is None:
        return
    future = asyncio.run_coroutine_threadsafe(save_run(**kwargs), _main_loop)
    try:
        future.result(timeout=10)
    except Exception:
        pass  # DB failure must never crash the test run


app = FastAPI(
    title="Web Auto Tester",
    description="Framework-agnostic automated testing for deployed web applications",
    version="1.0.0",
    lifespan=lifespan,
)

REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", "/tmp/web-auto-tester-reports"))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job store (active runs only; history lives in DB)
jobs: dict[str, dict] = {}

_ansi_re = re.compile(r'\x1b\[[0-9;]*m')


# ── Log capture ───────────────────────────────────────────────────────────────
class _LogCapture(io.TextIOBase):
    def __init__(self, job_id: str, original_stdout):
        self.job_id = job_id
        self.original = original_stdout
        self._lock = threading.Lock()

    def write(self, text):
        if text and text.strip():
            clean = _ansi_re.sub('', text).strip()
            if clean:
                with self._lock:
                    if self.job_id in jobs:
                        jobs[self.job_id]["logs"].append({
                            "ts": round(time.time(), 2),
                            "msg": clean,
                        })
        if self.original:
            self.original.write(text)
        return len(text) if text else 0

    def flush(self):
        if self.original:
            self.original.flush()


# ── Request / Response models ─────────────────────────────────────────────────
class TestRequest(BaseModel):
    url: str
    max_pages: int = 5
    max_depth: int = 2
    browser: str = "chromium"
    timeout: int = 20000


class TestResponse(BaseModel):
    job_id: str
    status: str
    message: str


# ── Background test job ───────────────────────────────────────────────────────
def _run_test_job(job_id: str, req: TestRequest):
    original_stdout = sys.stdout
    log_capture = _LogCapture(job_id, original_stdout)
    sys.stdout = log_capture

    started_at = time.time()

    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = started_at
        jobs[job_id]["progress"] = {"phase": "starting", "detail": "Initializing..."}

        url = req.url
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        output_dir = str(REPORTS_DIR / job_id)

        runner = AutoTestRunner(
            base_url=url,
            max_pages=req.max_pages,
            max_depth=req.max_depth,
            headless=True,
            browser=req.browser,
            output_dir=output_dir,
            screenshots=False,
            timeout=req.timeout,
            low_memory=True,
        )

        report = runner.run()

        result = {
            "total_tests": report.total_tests,
            "passed": report.total_passed,
            "failed": report.total_failed,
            "warnings": report.total_warnings,
            "pass_rate": round(report.pass_rate, 1),
            "duration": round(report.duration_seconds, 1),
            "pages_tested": len(report.pages),
            "framework": report.site_framework.name.value,
            "framework_version": report.site_framework.version,
        }

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = time.time()
        jobs[job_id]["progress"] = {"phase": "done", "detail": "All tests complete"}
        jobs[job_id]["result"] = result

        # Load the JSON report written to disk
        json_path = Path(output_dir) / "report.json"
        report_json_str = None
        if json_path.exists():
            report_json_str = json_path.read_text(encoding="utf-8")

        # Persist to DB — schedule on main event loop from this thread
        _save_run_threadsafe(
            run_id=job_id,
            url=url,
            mode="lite",
            status="completed",
            framework=report.site_framework.name.value,
            framework_version=report.site_framework.version,
            started_at=started_at,
            duration_seconds=round(report.duration_seconds, 1),
            total_pages=len(report.pages),
            total_tests=report.total_tests,
            passed=report.total_passed,
            failed=report.total_failed,
            warnings=report.total_warnings,
            pass_rate=round(report.pass_rate, 1),
            report_json=report_json_str,
        )

    except Exception as e:
        err = str(e)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = err
        jobs[job_id]["completed_at"] = time.time()
        jobs[job_id]["progress"] = {"phase": "error", "detail": err}

        _save_run_threadsafe(
            run_id=job_id,
            url=req.url,
            mode="lite",
            status="failed",
            framework=None,
            framework_version=None,
            started_at=started_at,
            duration_seconds=round(time.time() - started_at, 1),
            total_pages=0,
            total_tests=0,
            passed=0,
            failed=0,
            warnings=0,
            pass_rate=0.0,
            error_msg=err,
        )

    finally:
        sys.stdout = original_stdout


# ── API: Test execution ───────────────────────────────────────────────────────
@app.post("/api/test", response_model=TestResponse)
async def start_test(req: TestRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "queued",
        "url": req.url,
        "created_at": time.time(),
        "logs": [],
        "progress": {"phase": "queued", "detail": "Waiting to start..."},
    }
    background_tasks.add_task(_run_test_job, job_id, req)
    return TestResponse(
        job_id=job_id,
        status="queued",
        message=f"Test queued for {req.url}. Poll /api/test/{job_id} for status.",
    )


@app.get("/api/test/{job_id}")
async def get_test_status(job_id: str):
    if job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    job = jobs[job_id]
    return {
        "status": job["status"],
        "url": job.get("url"),
        "progress": job.get("progress"),
        "log_count": len(job.get("logs", [])),
        "result": job.get("result"),
        "error": job.get("error"),
    }


@app.get("/api/test/{job_id}/logs")
async def get_test_logs(job_id: str, since: int = 0):
    if job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    all_logs = jobs[job_id].get("logs", [])
    return {
        "status": jobs[job_id]["status"],
        "total": len(all_logs),
        "logs": all_logs[since:],
    }


@app.get("/api/test/{job_id}/report")
async def get_test_report(job_id: str):
    """Serve HTML report — from disk if available, else 404."""
    report_path = REPORTS_DIR / job_id / "report.html"
    if report_path.exists():
        return FileResponse(str(report_path), media_type="text/html")
    return JSONResponse(status_code=404, content={"error": "Report file not found"})


@app.get("/api/test/{job_id}/json")
async def get_test_json(job_id: str):
    """Serve JSON report — from disk or DB."""
    json_path = REPORTS_DIR / job_id / "report.json"
    if json_path.exists():
        return JSONResponse(content=json.loads(json_path.read_text("utf-8")))
    # Fall back to DB
    run = await get_run(job_id)
    if run and run.get("report_json"):
        return JSONResponse(content=run["report_json"])
    return JSONResponse(status_code=404, content={"error": "Report not found"})


# ── API: History (DB-backed) ──────────────────────────────────────────────────
@app.get("/api/reports")
async def list_reports(limit: int = 50):
    """List all persisted test runs, newest first."""
    runs = await list_runs(limit=limit)
    return {"runs": runs}


@app.get("/api/reports/{run_id}")
async def get_report(run_id: str):
    """Get full details of a persisted run including its JSON report."""
    run = await get_run(run_id)
    if not run:
        return JSONResponse(status_code=404, content={"error": "Run not found"})
    return run


# ── API: Health ───────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    from web_auto_tester.database import DATABASE_URL
    db_type = "postgresql" if "postgresql" in DATABASE_URL else "sqlite"
    return {"status": "healthy", "service": "web-auto-tester", "version": "1.0.0", "db": db_type}


# ── Web UI ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Web Auto Tester</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f1117; color: #e1e4ed; min-height: 100vh;
    display: flex; flex-direction: column; align-items: center;
  }
  .container { max-width: 1200px; width: 100%; padding: 40px 24px; }
  .container-narrow { max-width: 860px; margin: 0 auto; }
  h1 { font-size: 2.5rem; text-align: center; margin-bottom: 8px; }
  h1 span { color: #6366f1; }
  .subtitle { text-align: center; color: #8b8fa3; margin-bottom: 40px; font-size: 1.1rem; }
  .card {
    background: #1a1d27; border: 1px solid #2e3348; border-radius: 12px;
    padding: 32px; margin-bottom: 24px;
  }
  .card-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 18px; color: #c7cbe0; display: flex; align-items: center; gap: 8px; }
  .card-title .dot { width: 8px; height: 8px; border-radius: 50%; background: #6366f1; }
  label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 0.95rem; }
  input[type="text"], input[type="number"], select {
    width: 100%; padding: 12px 16px; background: #242836; border: 1px solid #2e3348;
    border-radius: 8px; color: #e1e4ed; font-size: 1rem; margin-bottom: 16px;
    outline: none; transition: border-color 0.2s;
  }
  input:focus, select:focus { border-color: #6366f1; }
  .row { display: flex; gap: 16px; }
  .row > div { flex: 1; }

  button.primary {
    width: 100%; padding: 14px; background: #6366f1; color: white; border: none;
    border-radius: 8px; font-size: 1.1rem; font-weight: 600; cursor: pointer;
    transition: all 0.2s;
  }
  button.primary:hover:not(:disabled) { background: #5558e6; }
  button.primary:disabled {
    background: #2a2d4a; color: #6b6e8a; cursor: not-allowed; border: 1px solid #3d3f5c;
  }
  button.primary .btn-spinner {
    display: inline-block; width: 18px; height: 18px;
    border: 2.5px solid rgba(255,255,255,0.2); border-top-color: #fff;
    border-radius: 50%; animation: spin 0.7s linear infinite;
    vertical-align: middle; margin-right: 10px;
  }

  #status { margin-top: 24px; padding: 20px; border-radius: 8px; display: none; border: 1px solid #2e3348; }
  #status.running { background: #12142a; border-color: #6366f1; }
  #status.completed { background: #0f2a1f; border-color: #22c55e; }
  #status.failed { background: #2a0f0f; border-color: #ef4444; }

  .status-header { font-weight: 600; font-size: 1.1rem; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; }
  .phase-badge {
    display: inline-block; padding: 3px 10px; border-radius: 10px;
    font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
  }
  .phase-badge.discovery { background: #1e2a5e; color: #818cf8; }
  .phase-badge.analyzing { background: #2a1e5e; color: #a78bfa; }
  .phase-badge.reporting { background: #1e3a2e; color: #6ee7b7; }
  .phase-badge.starting { background: #2e3348; color: #8b8fa3; }

  .progress-bar-wrap { width: 100%; height: 6px; background: #242836; border-radius: 3px; margin: 12px 0 16px 0; overflow: hidden; }
  .progress-bar { height: 100%; background: linear-gradient(90deg, #6366f1, #818cf8); border-radius: 3px; transition: width 0.4s ease; animation: pulse-glow 1.5s ease-in-out infinite; }
  @keyframes pulse-glow { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }

  .log-console {
    background: #0a0c14; border: 1px solid #1e2030; border-radius: 8px;
    padding: 0; margin-top: 14px;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 0.8rem; max-height: 320px; overflow-y: auto;
  }
  .log-console-header {
    display: flex; align-items: center; gap: 8px; padding: 8px 14px;
    border-bottom: 1px solid #1e2030; background: #0e1018;
    border-radius: 8px 8px 0 0; position: sticky; top: 0; z-index: 1;
  }
  .log-console-header .dot { width: 8px; height: 8px; border-radius: 50%; }
  .log-console-header .dot.red { background: #ef4444; }
  .log-console-header .dot.yellow { background: #f59e0b; }
  .log-console-header .dot.green { background: #22c55e; }
  .log-console-header span { color: #6b6e8a; font-size: 0.75rem; margin-left: auto; }
  .log-lines { padding: 10px 14px; }
  .log-line { padding: 2px 0; line-height: 1.6; color: #a0a4b8; word-break: break-word; }
  .log-line .log-ts { color: #4a4d65; margin-right: 8px; font-size: 0.7rem; }
  .log-line.highlight { color: #e1e4ed; font-weight: 500; }
  .log-line.success { color: #22c55e; }
  .log-line.error { color: #ef4444; }
  .log-line.warning { color: #f59e0b; }
  .log-line.phase { color: #818cf8; font-weight: 600; padding: 4px 0; }

  .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; margin-top: 14px; }
  .metric { text-align: center; padding: 14px 8px; background: #242836; border-radius: 8px; border: 1px solid #2e3348; }
  .metric .value { font-size: 1.5rem; font-weight: 700; }
  .metric .label { font-size: 0.75rem; color: #8b8fa3; margin-top: 4px; }
  .pass { color: #22c55e; }
  .fail { color: #ef4444; }
  .warn { color: #f59e0b; }

  .links { margin-top: 16px; display: flex; gap: 12px; flex-wrap: wrap; }
  .links a {
    display: inline-block; padding: 10px 20px; background: #6366f1; color: white;
    text-decoration: none; border-radius: 6px; font-weight: 500; transition: background 0.2s;
  }
  .links a:hover { background: #5558e6; }
  .links a.secondary { background: #242836; border: 1px solid #2e3348; color: #c7cbe0; }
  .links a.secondary:hover { background: #2e3348; }

  .spinner { display: inline-block; width: 18px; height: 18px; border: 2.5px solid #2e3348;
    border-top-color: #6366f1; border-radius: 50%; animation: spin 0.8s linear infinite;
    vertical-align: middle; margin-right: 8px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .elapsed { color: #6b6e8a; font-size: 0.85rem; float: right; }

  /* ── History table ── */
  .table-scroll { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .history-table {
    width: 100%; min-width: 900px; border-collapse: collapse;
    margin-top: 4px; font-size: 0.88rem;
  }
  .history-table th {
    padding: 11px 16px; text-align: left; border-bottom: 2px solid #2e3348;
    color: #8b8fa3; font-size: 0.75rem; text-transform: uppercase;
    font-weight: 700; letter-spacing: 0.6px; white-space: nowrap;
    background: #1a1d27;
  }
  .history-table td {
    padding: 13px 16px; border-bottom: 1px solid #1e2130;
    vertical-align: middle; white-space: nowrap;
  }
  .history-table tr:last-child td { border-bottom: none; }
  .history-table tr:hover td { background: #1e2130; }
  .history-table .url-cell {
    max-width: 260px; overflow: hidden; text-overflow: ellipsis;
    white-space: nowrap; color: #c7cbe0;
  }
  .history-table .report-cell { white-space: nowrap; min-width: 100px; }
  .history-table .fw-cell { min-width: 110px; }
  .history-table .date-cell { min-width: 120px; color: #8b8fa3; }
  .history-table .num-cell { text-align: center; min-width: 60px; }
  .history-table .status-cell { min-width: 90px; }
  .badge { padding: 3px 10px; border-radius: 10px; font-size: 0.78rem; font-weight: 700; }
  .badge.completed { background: #0f2a1f; color: #22c55e; }
  .badge.failed { background: #2a0f0f; color: #ef4444; }
  .badge.running { background: #1e2a5e; color: #818cf8; }
  .badge.queued { background: #2e3348; color: #8b8fa3; }
  .pass-rate-cell { font-weight: 700; }
  .pass-rate-cell.good { color: #22c55e; }
  .pass-rate-cell.mid { color: #f59e0b; }
  .pass-rate-cell.bad { color: #ef4444; }
  .action-link { color: #818cf8; text-decoration: none; font-size: 0.85rem; }
  .action-link:hover { color: #6366f1; text-decoration: underline; }
  .fw-tag { font-size: 0.78rem; color: #6b6e8a; }
  .empty-history { text-align: center; padding: 32px; color: #4a4d65; }
  .empty-history .empty-icon { font-size: 2rem; margin-bottom: 8px; }
  .db-badge {
    display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 0.72rem;
    background: #1e2a5e; color: #818cf8; font-weight: 600; margin-left: 8px; vertical-align: middle;
  }
</style>
</head>
<body>
<div class="container">
  <h1>Web <span>Auto</span> Tester</h1>
  <p class="subtitle">Framework-agnostic automated testing for any deployed web application</p>

  <!-- Run Tests Card -->
  <div class="card container-narrow">
    <div class="card-title"><div class="dot"></div> New Test Run</div>
    <label for="url">Target URL</label>
    <input type="text" id="url" placeholder="https://your-app.com" autofocus>

    <div class="row">
      <div>
        <label for="maxPages">Max Pages</label>
        <input type="number" id="maxPages" value="5" min="1" max="20">
      </div>
      <div>
        <label for="maxDepth">Max Depth</label>
        <input type="number" id="maxDepth" value="2" min="1" max="5">
      </div>
    </div>

    <button class="primary" id="runBtn" onclick="runTest()">Run Tests</button>

    <div id="status"></div>
  </div>

  <!-- Test History Card -->
  <div class="card">
    <div class="card-title">
      <div class="dot"></div>
      Test History
      <span class="db-badge" id="dbBadge">SQLite</span>
      <span style="margin-left:auto; font-size:0.82rem; color:#6b6e8a; font-weight:400;" id="historyCount"></span>
    </div>
    <div id="historyList">
      <div class="empty-history"><div class="empty-icon">&#9112;</div><div>No test runs yet</div></div>
    </div>
  </div>
</div>

<script>
let pollInterval = null;
let logOffset = 0;
let testStartTime = 0;
let elapsedInterval = null;
let currentJobId = null;

function setRunning(isRunning) {
  const btn = document.getElementById('runBtn');
  const urlInput = document.getElementById('url');
  if (isRunning) {
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-spinner"></span> Testing in progress...';
    urlInput.disabled = true;
    document.querySelectorAll('.row input').forEach(el => el.disabled = true);
  } else {
    btn.disabled = false;
    btn.innerHTML = 'Run Tests';
    urlInput.disabled = false;
    document.querySelectorAll('.row input').forEach(el => el.disabled = false);
  }
}

function formatElapsed(seconds) {
  const m = Math.floor(seconds / 60), s = Math.floor(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function fmtDate(ts) {
  if (!ts) return '-';
  const d = new Date(ts * 1000);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
    + ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

function classifyLog(msg) {
  const lower = msg.toLowerCase();
  if (lower.includes('phase 1') || lower.includes('phase 2') || lower.includes('phase 3')) return 'phase';
  if (lower.includes('passed') || msg.includes('+')) return 'success';
  if (lower.includes('error') || lower.includes('failed') || msg.includes('!')) return 'error';
  if (lower.includes('warning') || msg.includes('~')) return 'warning';
  if (lower.includes('====') || lower.includes('complete') || lower.includes('framework:') || lower.includes('found')) return 'highlight';
  return '';
}

function detectPhase(msg) {
  if (msg.includes('Phase 1') || msg.includes('Discovering')) return 'discovery';
  if (msg.includes('Phase 2') || msg.includes('Running') || msg.includes('test suite')) return 'analyzing';
  if (msg.includes('Phase 3') || msg.includes('Generating report')) return 'reporting';
  if (msg.includes('Launching') || msg.includes('Initializ')) return 'starting';
  return null;
}

async function runTest() {
  const url = document.getElementById('url').value.trim();
  if (!url) { alert('Please enter a URL'); return; }

  setRunning(true);
  logOffset = 0;
  testStartTime = Date.now();

  const res = await fetch('/api/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      max_pages: parseInt(document.getElementById('maxPages').value),
      max_depth: parseInt(document.getElementById('maxDepth').value),
    })
  });

  const data = await res.json();
  currentJobId = data.job_id;

  showStatus('running', `
    <div class="status-header">
      <div class="spinner"></div>
      <span>Testing <strong>${escHtml(url)}</strong></span>
      <span class="elapsed" id="elapsed">0s</span>
    </div>
    <div style="display:flex; align-items:center; gap:10px; margin-top:6px;">
      <span class="phase-badge starting" id="phaseBadge">STARTING</span>
      <span id="phaseDetail" style="color:#8b8fa3; font-size:0.85rem;">Initializing...</span>
    </div>
    <div class="progress-bar-wrap"><div class="progress-bar" id="progressBar" style="width:5%"></div></div>
    <div class="log-console" id="logConsole">
      <div class="log-console-header">
        <div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div>
        <span id="logCount">0 log entries</span>
      </div>
      <div class="log-lines" id="logLines"></div>
    </div>
  `);

  if (elapsedInterval) clearInterval(elapsedInterval);
  elapsedInterval = setInterval(() => {
    const el = document.getElementById('elapsed');
    if (el) el.textContent = formatElapsed((Date.now() - testStartTime) / 1000);
  }, 1000);

  pollJob(data.job_id);
}

function pollJob(jobId) {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(async () => {
    const [statusRes, logsRes] = await Promise.all([
      fetch(`/api/test/${jobId}`),
      fetch(`/api/test/${jobId}/logs?since=${logOffset}`)
    ]);
    const statusData = await statusRes.json();
    const logsData = await logsRes.json();

    if (logsData.logs && logsData.logs.length > 0) {
      const logLines = document.getElementById('logLines');
      const logConsole = document.getElementById('logConsole');
      if (logLines) {
        for (const log of logsData.logs) {
          const cls = classifyLog(log.msg);
          const div = document.createElement('div');
          div.className = 'log-line' + (cls ? ' ' + cls : '');
          const ts = new Date(log.ts * 1000);
          const timeStr = ts.toLocaleTimeString('en-US', {hour12:false, hour:'2-digit', minute:'2-digit', second:'2-digit'});
          div.innerHTML = `<span class="log-ts">${timeStr}</span>${escHtml(log.msg)}`;
          logLines.appendChild(div);
          const phase = detectPhase(log.msg);
          if (phase) updatePhase(phase, log.msg);
        }
        logOffset = logsData.total;
        if (logConsole) logConsole.scrollTop = logConsole.scrollHeight;
        const countEl = document.getElementById('logCount');
        if (countEl) countEl.textContent = `${logsData.total} log entries`;
      }
    }

    updateProgressFromLogs(statusData, logsData.total);

    if (statusData.status === 'completed') {
      clearInterval(pollInterval);
      if (elapsedInterval) clearInterval(elapsedInterval);
      const r = statusData.result;
      const elapsed = formatElapsed((Date.now() - testStartTime) / 1000);
      showStatus('completed', `
        <div class="status-header">
          <span class="pass" style="font-size:1.3rem;">&#10003;</span>
          <span>Tests Completed</span>
          <span class="elapsed">${elapsed}</span>
        </div>
        <div class="metrics">
          <div class="metric"><div class="value">${r.pages_tested}</div><div class="label">Pages</div></div>
          <div class="metric"><div class="value">${r.total_tests}</div><div class="label">Total Tests</div></div>
          <div class="metric"><div class="value pass">${r.passed}</div><div class="label">Passed</div></div>
          <div class="metric"><div class="value fail">${r.failed}</div><div class="label">Failed</div></div>
          <div class="metric"><div class="value warn">${r.warnings}</div><div class="label">Warnings</div></div>
          <div class="metric"><div class="value">${r.pass_rate}%</div><div class="label">Pass Rate</div></div>
          <div class="metric"><div class="value">${r.duration}s</div><div class="label">Duration</div></div>
          <div class="metric"><div class="value" style="font-size:1rem;">${r.framework}</div><div class="label">Framework</div></div>
        </div>
        <div class="links">
          <a href="/api/test/${jobId}/report" target="_blank">View Full Report</a>
          <a href="/api/test/${jobId}/json" target="_blank" class="secondary">JSON Report</a>
        </div>
      `);
      setRunning(false);
      loadHistory();

    } else if (statusData.status === 'failed') {
      clearInterval(pollInterval);
      if (elapsedInterval) clearInterval(elapsedInterval);
      showStatus('failed', `
        <div class="status-header">
          <span class="fail" style="font-size:1.2rem;">&#10007;</span>
          <span>Test Run Failed</span>
        </div>
        <p style="margin-top:8px; color:#ef4444;">${escHtml(statusData.error || 'Unknown error')}</p>
      `);
      setRunning(false);
      loadHistory();
    }
  }, 2000);
}

function updatePhase(phase, msg) {
  const badge = document.getElementById('phaseBadge');
  const detail = document.getElementById('phaseDetail');
  if (!badge || !detail) return;
  const labels = { starting:'STARTING', discovery:'DISCOVERY', analyzing:'ANALYZING', reporting:'REPORTING' };
  badge.className = 'phase-badge ' + phase;
  badge.textContent = labels[phase] || phase.toUpperCase();
  let shortMsg = msg;
  if (msg.includes(':')) shortMsg = msg.split(':').slice(1).join(':').trim();
  if (shortMsg.length > 80) shortMsg = shortMsg.substring(0, 77) + '...';
  detail.textContent = shortMsg || msg;
}

function updateProgressFromLogs(statusData, logCount) {
  const bar = document.getElementById('progressBar');
  if (!bar) return;
  let pct = Math.min(95, 5 + (logCount * 2));
  if (statusData.progress) {
    const p = statusData.progress.phase;
    if (p === 'starting') pct = Math.max(pct, 5);
    else if (p === 'discovery') pct = Math.max(pct, 15);
    else if (p === 'analyzing') pct = Math.max(pct, 35);
    else if (p === 'reporting') pct = Math.max(pct, 85);
    else if (p === 'done') pct = 100;
  }
  bar.style.width = pct + '%';
  if (pct >= 100) bar.style.animation = 'none';
}

function showStatus(cls, html) {
  const el = document.getElementById('status');
  el.className = cls;
  el.innerHTML = html;
  el.style.display = 'block';
}

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

function passRateClass(rate) {
  if (rate >= 75) return 'good';
  if (rate >= 50) return 'mid';
  return 'bad';
}

async function loadHistory() {
  try {
    // Also check health to get DB type
    const [histRes, healthRes] = await Promise.all([
      fetch('/api/reports?limit=50'),
      fetch('/health'),
    ]);
    const histData = await histRes.json();
    const healthData = await healthRes.json();

    // Update DB badge
    const badge = document.getElementById('dbBadge');
    if (badge) {
      badge.textContent = healthData.db === 'postgresql' ? 'PostgreSQL' : 'SQLite';
      badge.style.background = healthData.db === 'postgresql' ? '#0f2a3a' : '#1e2a5e';
      badge.style.color = healthData.db === 'postgresql' ? '#38bdf8' : '#818cf8';
    }

    const runs = histData.runs || [];
    const el = document.getElementById('historyList');
    const countEl = document.getElementById('historyCount');
    if (countEl) countEl.textContent = runs.length ? `${runs.length} run${runs.length !== 1 ? 's' : ''}` : '';

    if (!runs.length) {
      el.innerHTML = `<div class="empty-history"><div class="empty-icon">&#9112;</div><div>No test runs yet — run your first test above</div></div>`;
      return;
    }

    el.innerHTML = `
      <div class="table-scroll">
      <table class="history-table">
        <thead>
          <tr>
            <th style="min-width:200px;">URL</th>
            <th style="min-width:130px;">Framework</th>
            <th style="min-width:95px;">Pass Rate</th>
            <th style="min-width:65px;">Tests</th>
            <th style="min-width:65px;">Pages</th>
            <th style="min-width:85px;">Duration</th>
            <th style="min-width:140px;">Date</th>
            <th style="min-width:105px;">Status</th>
            <th style="min-width:115px;">Report</th>
          </tr>
        </thead>
        <tbody>
          ${runs.map(r => {
            const rate = r.pass_rate || 0;
            const rateClass = passRateClass(rate);
            const fw = r.framework || '—';
            const fwVer = r.framework_version ? ` <span class="fw-tag">v${escHtml(r.framework_version)}</span>` : '';
            const reportLink = r.status === 'completed'
              ? `<a class="action-link" href="/api/test/${r.id}/report" target="_blank">HTML</a>
                 <span style="color:#3d4060; margin:0 5px;">|</span>
                 <a class="action-link" href="/api/test/${r.id}/json" target="_blank">JSON</a>`
              : r.error_msg
                ? `<span style="color:#6b6e8a;font-size:0.78rem;" title="${escHtml(r.error_msg)}">—</span>`
                : '—';
            return `<tr>
              <td class="url-cell" title="${escHtml(r.url)}">${escHtml(r.url)}</td>
              <td class="fw-cell">${escHtml(fw)}${fwVer}</td>
              <td class="pass-rate-cell ${rateClass}">${r.status === 'completed' ? rate.toFixed(1) + '%' : '—'}</td>
              <td class="num-cell">${r.total_tests || '—'}</td>
              <td class="num-cell">${r.total_pages || '—'}</td>
              <td class="num-cell">${r.duration_seconds ? r.duration_seconds + 's' : '—'}</td>
              <td class="date-cell">${fmtDate(r.started_at)}</td>
              <td class="status-cell"><span class="badge ${r.status}">${r.status}</span></td>
              <td class="report-cell">${reportLink}</td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
      </div>`;
  } catch(e) {
    console.error('Failed to load history:', e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('url').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !document.getElementById('runBtn').disabled) runTest();
  });
  loadHistory();
});
</script>
</body>
</html>"""
