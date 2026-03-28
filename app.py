"""
FastAPI web service for Web Auto Tester.

Provides a web UI and REST API to run automated tests against any deployed web application.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from web_auto_tester.runner import AutoTestRunner

app = FastAPI(
    title="Web Auto Tester",
    description="Framework-agnostic automated testing for deployed web applications",
    version="1.0.0",
)

# Directory to store test reports
REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", "/tmp/web-auto-tester-reports"))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job store
jobs: dict[str, dict] = {}


class TestRequest(BaseModel):
    url: str
    max_pages: int = 20
    max_depth: int = 3
    browser: str = "chromium"
    timeout: int = 30000


class TestResponse(BaseModel):
    job_id: str
    status: str
    message: str


def _run_test_job(job_id: str, req: TestRequest):
    """Run tests in background and update job status."""
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = time.time()

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
            screenshots=True,
            timeout=req.timeout,
        )

        report = runner.run()

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = time.time()
        jobs[job_id]["result"] = {
            "total_tests": report.total_tests,
            "passed": report.total_passed,
            "failed": report.total_failed,
            "warnings": report.total_warnings,
            "pass_rate": round(report.pass_rate, 1),
            "duration": round(report.duration_seconds, 1),
            "pages_tested": len(report.pages),
            "framework": report.site_framework.name.value,
        }

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = time.time()


# ── API Endpoints ────────────────────────────────────────────────────────────

@app.post("/api/test", response_model=TestResponse)
async def start_test(req: TestRequest, background_tasks: BackgroundTasks):
    """Start a new test run. Returns a job ID to poll for results."""
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "queued",
        "url": req.url,
        "created_at": time.time(),
    }
    background_tasks.add_task(_run_test_job, job_id, req)
    return TestResponse(
        job_id=job_id,
        status="queued",
        message=f"Test queued for {req.url}. Poll /api/test/{job_id} for status.",
    )


@app.get("/api/test/{job_id}")
async def get_test_status(job_id: str):
    """Get the status and results of a test run."""
    if job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    return jobs[job_id]


@app.get("/api/test/{job_id}/report")
async def get_test_report(job_id: str):
    """Get the HTML report for a completed test run."""
    if job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    if jobs[job_id]["status"] != "completed":
        return JSONResponse(status_code=400, content={"error": "Test not completed yet"})

    report_path = REPORTS_DIR / job_id / "report.html"
    if not report_path.exists():
        return JSONResponse(status_code=404, content={"error": "Report file not found"})
    return FileResponse(str(report_path), media_type="text/html")


@app.get("/api/test/{job_id}/json")
async def get_test_json(job_id: str):
    """Get the JSON report for a completed test run."""
    if job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    if jobs[job_id]["status"] != "completed":
        return JSONResponse(status_code=400, content={"error": "Test not completed yet"})

    json_path = REPORTS_DIR / job_id / "report.json"
    if not json_path.exists():
        return JSONResponse(status_code=404, content={"error": "JSON report not found"})

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(content=data)


@app.get("/api/jobs")
async def list_jobs():
    """List all test jobs."""
    return {
        "jobs": [
            {"job_id": jid, "url": j.get("url"), "status": j["status"]}
            for jid, j in sorted(jobs.items(), key=lambda x: x[1].get("created_at", 0), reverse=True)
        ]
    }


@app.get("/health")
async def health():
    """Health check endpoint for Render."""
    return {"status": "healthy", "service": "web-auto-tester", "version": "1.0.0"}


# ── Web UI ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home():
    """Web UI for submitting tests and viewing results."""
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
  .container { max-width: 800px; width: 100%; padding: 40px 20px; }
  h1 { font-size: 2.5rem; text-align: center; margin-bottom: 8px; }
  h1 span { color: #6366f1; }
  .subtitle { text-align: center; color: #8b8fa3; margin-bottom: 40px; font-size: 1.1rem; }
  .card {
    background: #1a1d27; border: 1px solid #2e3348; border-radius: 12px;
    padding: 32px; margin-bottom: 24px;
  }
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
    transition: background 0.2s;
  }
  button.primary:hover { background: #5558e6; }
  button.primary:disabled { background: #3d3f5c; cursor: not-allowed; }
  #status {
    margin-top: 24px; padding: 20px; border-radius: 8px; display: none;
    border: 1px solid #2e3348;
  }
  #status.running { background: #1a1d27; border-color: #6366f1; }
  #status.completed { background: #0f2a1f; border-color: #22c55e; }
  #status.failed { background: #2a0f0f; border-color: #ef4444; }
  .status-header { font-weight: 600; font-size: 1.1rem; margin-bottom: 8px; }
  .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-top: 12px; }
  .metric { text-align: center; padding: 12px; background: #242836; border-radius: 8px; }
  .metric .value { font-size: 1.5rem; font-weight: 700; }
  .metric .label { font-size: 0.8rem; color: #8b8fa3; margin-top: 4px; }
  .pass { color: #22c55e; }
  .fail { color: #ef4444; }
  .warn { color: #f59e0b; }
  .links { margin-top: 16px; display: flex; gap: 12px; }
  .links a {
    display: inline-block; padding: 10px 20px; background: #6366f1; color: white;
    text-decoration: none; border-radius: 6px; font-weight: 500;
  }
  .links a:hover { background: #5558e6; }
  .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid #2e3348;
    border-top-color: #6366f1; border-radius: 50%; animation: spin 0.8s linear infinite;
    vertical-align: middle; margin-right: 8px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .jobs-table { width: 100%; border-collapse: collapse; margin-top: 16px; }
  .jobs-table th, .jobs-table td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #2e3348; }
  .jobs-table th { color: #8b8fa3; font-size: 0.85rem; text-transform: uppercase; }
  .badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
  .badge.queued { background: #2e3348; color: #8b8fa3; }
  .badge.running { background: #1e2a5e; color: #818cf8; }
  .badge.completed { background: #0f2a1f; color: #22c55e; }
  .badge.failed { background: #2a0f0f; color: #ef4444; }
</style>
</head>
<body>
<div class="container">
  <h1>Web <span>Auto</span> Tester</h1>
  <p class="subtitle">Framework-agnostic automated testing for any deployed web application</p>

  <div class="card">
    <label for="url">Target URL</label>
    <input type="text" id="url" placeholder="https://your-app.com" autofocus>

    <div class="row">
      <div>
        <label for="maxPages">Max Pages</label>
        <input type="number" id="maxPages" value="20" min="1" max="100">
      </div>
      <div>
        <label for="maxDepth">Max Depth</label>
        <input type="number" id="maxDepth" value="3" min="1" max="10">
      </div>
      <div>
        <label for="browser">Browser</label>
        <select id="browser">
          <option value="chromium">Chromium</option>
          <option value="firefox">Firefox</option>
        </select>
      </div>
    </div>

    <button class="primary" id="runBtn" onclick="runTest()">Run Tests</button>

    <div id="status"></div>
  </div>

  <div class="card">
    <h3 style="margin-bottom: 12px;">Recent Jobs</h3>
    <div id="jobsList"><em style="color: #8b8fa3;">No jobs yet</em></div>
  </div>
</div>

<script>
let pollInterval = null;

async function runTest() {
  const url = document.getElementById('url').value.trim();
  if (!url) { alert('Please enter a URL'); return; }

  const btn = document.getElementById('runBtn');
  btn.disabled = true;
  btn.textContent = 'Starting...';

  const res = await fetch('/api/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      max_pages: parseInt(document.getElementById('maxPages').value),
      max_depth: parseInt(document.getElementById('maxDepth').value),
      browser: document.getElementById('browser').value,
    })
  });

  const data = await res.json();
  btn.textContent = 'Run Tests';
  btn.disabled = false;

  showStatus('running', `<div class="spinner"></div> Testing <strong>${url}</strong>...`);
  pollJob(data.job_id);
}

function pollJob(jobId) {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(async () => {
    const res = await fetch(`/api/test/${jobId}`);
    const data = await res.json();

    if (data.status === 'completed') {
      clearInterval(pollInterval);
      const r = data.result;
      showStatus('completed', `
        <div class="status-header pass">Tests Completed</div>
        <div class="metrics">
          <div class="metric"><div class="value">${r.pages_tested}</div><div class="label">Pages</div></div>
          <div class="metric"><div class="value">${r.total_tests}</div><div class="label">Total Tests</div></div>
          <div class="metric"><div class="value pass">${r.passed}</div><div class="label">Passed</div></div>
          <div class="metric"><div class="value fail">${r.failed}</div><div class="label">Failed</div></div>
          <div class="metric"><div class="value warn">${r.warnings}</div><div class="label">Warnings</div></div>
          <div class="metric"><div class="value">${r.pass_rate}%</div><div class="label">Pass Rate</div></div>
          <div class="metric"><div class="value">${r.duration}s</div><div class="label">Duration</div></div>
          <div class="metric"><div class="value">${r.framework}</div><div class="label">Framework</div></div>
        </div>
        <div class="links">
          <a href="/api/test/${jobId}/report" target="_blank">View Full Report</a>
          <a href="/api/test/${jobId}/json" target="_blank">JSON Report</a>
        </div>
      `);
      loadJobs();
    } else if (data.status === 'failed') {
      clearInterval(pollInterval);
      showStatus('failed', `<div class="status-header fail">Test Failed</div><p>${data.error || 'Unknown error'}</p>`);
      loadJobs();
    }
  }, 3000);
}

function showStatus(cls, html) {
  const el = document.getElementById('status');
  el.className = cls;
  el.innerHTML = html;
  el.style.display = 'block';
}

async function loadJobs() {
  try {
    const res = await fetch('/api/jobs');
    const data = await res.json();
    const el = document.getElementById('jobsList');
    if (!data.jobs.length) { el.innerHTML = '<em style="color: #8b8fa3;">No jobs yet</em>'; return; }
    el.innerHTML = `<table class="jobs-table">
      <tr><th>Job ID</th><th>URL</th><th>Status</th><th>Action</th></tr>
      ${data.jobs.map(j => `<tr>
        <td><code>${j.job_id}</code></td>
        <td>${j.url}</td>
        <td><span class="badge ${j.status}">${j.status}</span></td>
        <td>${j.status === 'completed' ? `<a href="/api/test/${j.job_id}/report" target="_blank" style="color:#818cf8;">Report</a>` : '-'}</td>
      </tr>`).join('')}
    </table>`;
  } catch(e) {}
}

loadJobs();
</script>
</body>
</html>"""
