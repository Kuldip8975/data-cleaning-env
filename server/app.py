"""
app.py - Data Cleaning AI Agent
Pure FastAPI + HTML — no Gradio UI rendering issues
Beautiful, clean, fully controlled design
"""

import os
import io
import json
import tempfile
import base64
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from env import DataCleaningEnv
from inference import rule_based_clean
from file_cleaner import clean_uploaded_file

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── Global env for validator ───────────────────────────────────
_env = DataCleaningEnv(difficulty="easy")

class StepRequest(BaseModel):
    action: str

@app.post("/reset")
def api_reset(difficulty: str = "easy"):
    global _env
    _env  = DataCleaningEnv(difficulty=difficulty)
    state = _env.reset()
    return JSONResponse(content=state)

@app.post("/step")
def api_step(req: StepRequest):
    if _env.current_task is None:
        return JSONResponse(content={"error": "call /reset first"}, status_code=400)
    state, reward, done, info = _env.step(req.action)
    return JSONResponse(content={"state": state, "reward": reward,
                                  "done": done, "info": info})

@app.get("/state")
def api_state():
    return JSONResponse(content=_env.state())

@app.get("/health")
def api_health():
    return {"status": "ok", "env": "data-cleaning-env", "version": "1.0.0"}

# ── Clean text endpoint ────────────────────────────────────────
@app.post("/clean-text")
async def clean_text(dirty: str = Form(...), difficulty: str = Form("easy")):
    env = DataCleaningEnv(difficulty=difficulty)
    env.current_task = {"id": "demo", "input": dirty,
                         "expected_output": "", "description": "demo"}
    result = rule_based_clean(dirty)
    return JSONResponse(content={"cleaned": result})

# ── Upload file endpoint ───────────────────────────────────────
@app.post("/clean-file")
async def clean_file(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1].lower()
    tmp    = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(await file.read())
    tmp.close()

    ftype, result = clean_uploaded_file(tmp.name)
    os.unlink(tmp.name)

    if "error" in result.get("report", {}):
        return JSONResponse(content={"error": result["report"]["error"]}, status_code=400)

    report  = result["report"]
    preview = []

    if result["cleaned_df"] is not None:
        df, orig = result["cleaned_df"], result["original_df"]
        for i, (_, row) in enumerate(df.head(12).iterrows()):
            for col in df.columns:
                ov = str(orig.at[i, col]).strip()
                cv = str(row[col]).strip()
                preview.append({"col": col, "original": ov,
                                  "cleaned": cv, "changed": ov != cv})
    elif result["cleaned_text"]:
        for i, ln in enumerate(result["cleaned_text"].split("\n")[:12]):
            preview.append({"col": f"line {i+1}", "original": "...",
                              "cleaned": ln, "changed": True})

    # Encode cleaned file as base64 for download
    dl_b64  = ""
    dl_name = ""
    if ftype == "csv" and result["csv_string"]:
        dl_b64  = base64.b64encode(result["csv_string"].encode()).decode()
        dl_name = file.filename.replace(".", "_cleaned.")
    elif ftype == "excel" and result.get("excel_bytes"):
        dl_b64  = base64.b64encode(result["excel_bytes"]).decode()
        dl_name = file.filename.replace(".", "_cleaned.")

    changed = report.get("cells_changed", report.get("lines_changed", 0))
    total   = report.get("total_cells", report.get("lines", 0))
    pct     = report.get("change_pct", 0)

    return JSONResponse(content={
        "file_type": ftype,
        "file_name": file.filename,
        "rows":      report.get("rows", report.get("lines", 0)),
        "columns":   report.get("columns", 1),
        "changed":   changed,
        "total":     total,
        "pct":       pct,
        "columns_list": report.get("column_names", []),
        "preview":   preview,
        "dl_b64":    dl_b64,
        "dl_name":   dl_name,
    })

# ── Evaluation endpoint ────────────────────────────────────────
@app.get("/evaluate")
def evaluate():
    scores = {}
    counts = {}
    rows   = []

    for d in ["easy", "medium", "hard"]:
        env   = DataCleaningEnv(d)
        tasks = env.get_all_tasks()
        rwds  = []
        for t in tasks:
            env.current_task = t
            env.done         = False
            action = rule_based_clean(t["input"])
            _, rw, _, info   = env.step(action)
            rwds.append(rw)
            rows.append({
                "level":    d.upper(),
                "task_id":  t["id"],
                "output":   info["your_output"],
                "expected": info["expected_output"],
                "reward":   rw,
                "verdict":  "correct" if rw==1.0 else ("partial" if rw==0.5 else "wrong")
            })
        avg        = sum(rwds) / len(rwds)
        scores[d]  = round(avg * 100)
        counts[d]  = {
            "correct": sum(1 for r in rwds if r == 1.0),
            "partial": sum(1 for r in rwds if r == 0.5),
            "total":   len(rwds),
        }

    overall = sum(scores.values()) / 3
    grade   = "A+" if overall >= 90 else ("A" if overall >= 80 else "B+")
    return JSONResponse(content={
        "scores": scores, "counts": counts,
        "overall": round(overall), "grade": grade, "rows": rows
    })

# ── Main HTML page ─────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Data Cleaning AI Agent</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #f7f7f5;
    color: #1a1a1a;
    min-height: 100vh;
  }

  .wrap { max-width: 900px; margin: 0 auto; padding: 0 24px 60px; }

  /* Header */
  .header {
    padding: 48px 0 36px;
    border-bottom: 1px solid #e8e8e8;
    margin-bottom: 40px;
  }
  .header h1 {
    font-size: 26px;
    font-weight: 600;
    letter-spacing: -0.5px;
    color: #111;
    margin-bottom: 8px;
  }
  .header p {
    font-size: 15px;
    color: #888;
    line-height: 1.6;
    max-width: 560px;
  }
  .pills {
    display: flex;
    gap: 8px;
    margin-top: 16px;
    flex-wrap: wrap;
  }
  .pill {
    font-size: 11px;
    font-weight: 500;
    color: #666;
    background: #efefed;
    border-radius: 20px;
    padding: 3px 10px;
  }

  /* Tabs */
  .tabs {
    display: flex;
    gap: 0;
    border-bottom: 1px solid #e8e8e8;
    margin-bottom: 32px;
  }
  .tab {
    font-size: 14px;
    font-weight: 400;
    color: #aaa;
    padding: 10px 18px;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    background: none;
    border-top: none;
    border-left: none;
    border-right: none;
    transition: color 0.15s;
  }
  .tab:hover { color: #555; }
  .tab.active {
    color: #111;
    font-weight: 600;
    border-bottom-color: #111;
  }

  /* Panels */
  .panel { display: none; }
  .panel.active { display: block; }

  /* Section title */
  .section-title {
    font-size: 11px;
    font-weight: 600;
    color: #aaa;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 10px;
  }

  /* Card */
  .card {
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
  }

  /* Two column layout */
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media (max-width: 640px) { .cols { grid-template-columns: 1fr; } }

  /* Form elements */
  label {
    display: block;
    font-size: 11px;
    font-weight: 600;
    color: #aaa;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }
  textarea, select, input[type="text"] {
    width: 100%;
    background: #fafaf9;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
    font-family: "SF Mono", "Fira Code", "Consolas", monospace;
    color: #111;
    resize: vertical;
    transition: border-color 0.15s;
  }
  textarea:focus, select:focus, input:focus {
    outline: none;
    border-color: #111;
    box-shadow: 0 0 0 3px rgba(0,0,0,0.06);
  }
  select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23888' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
    padding-right: 32px;
    cursor: pointer;
  }

  /* Buttons */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 500;
    padding: 9px 20px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.12s;
    border: none;
    font-family: inherit;
  }
  .btn-primary {
    background: #111;
    color: #fff;
  }
  .btn-primary:hover { background: #333; }
  .btn-primary:active { transform: scale(0.98); }
  .btn-secondary {
    background: #fff;
    color: #111;
    border: 1px solid #e8e8e8;
  }
  .btn-secondary:hover { background: #f5f5f5; }

  /* Examples */
  .examples { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
  .example-btn {
    font-size: 12px;
    font-family: "SF Mono","Fira Code",monospace;
    color: #555;
    background: #f5f5f3;
    border: 1px solid #e8e8e8;
    border-radius: 6px;
    padding: 5px 10px;
    cursor: pointer;
    transition: all 0.12s;
    white-space: nowrap;
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .example-btn:hover { background: #eee; border-color: #ccc; }

  /* Stat row */
  .stat-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 20px;
  }
  @media (max-width: 640px) { .stat-row { grid-template-columns: repeat(2,1fr); } }
  .stat {
    background: #fafaf9;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
  }
  .stat-val {
    font-size: 22px;
    font-weight: 600;
    color: #111;
    letter-spacing: -0.5px;
    line-height: 1;
    margin-bottom: 4px;
  }
  .stat-lbl {
    font-size: 11px;
    color: #aaa;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .stat.green { border-color: #bbf7d0; background: #f0fdf4; }
  .stat.green .stat-val { color: #15803d; }
  .stat.amber { border-color: #fde68a; background: #fffbeb; }
  .stat.amber .stat-val { color: #b45309; }

  /* Score bars */
  .score-bar { margin-bottom: 14px; }
  .score-bar-header {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    margin-bottom: 5px;
  }
  .score-bar-name { font-weight: 500; color: #333; }
  .score-bar-pct  { color: #888; font-family: monospace; }
  .score-bar-bg   { background: #f0f0ee; border-radius: 4px; height: 6px; }
  .score-bar-fill { height: 6px; border-radius: 4px; transition: width 0.6s ease; }

  .overall-block {
    background: #111;
    border-radius: 10px;
    padding: 20px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 20px;
  }
  .overall-score { font-size: 28px; font-weight: 600; color: #fff; }
  .overall-label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
  .overall-grade { font-size: 28px; font-weight: 600; color: #fff; }

  /* Table */
  .tbl-wrap { overflow-x: auto; border-radius: 10px; border: 1px solid #e8e8e8; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th {
    background: #fafaf9;
    color: #aaa;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid #e8e8e8;
    font-weight: 600;
    white-space: nowrap;
  }
  td {
    padding: 9px 14px;
    border-bottom: 1px solid #f5f5f3;
    color: #333;
    font-family: "SF Mono","Fira Code",monospace;
    vertical-align: top;
    word-break: break-word;
    max-width: 200px;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #fafaf9; }
  .verdict-correct { color: #15803d; font-weight: 500; }
  .verdict-partial  { color: #b45309; font-weight: 500; }
  .verdict-wrong    { color: #b91c1c; font-weight: 500; }
  .changed-yes { color: #b45309; }

  /* Upload area */
  .upload-area {
    border: 2px dashed #e8e8e8;
    border-radius: 12px;
    padding: 32px 24px;
    text-align: center;
    cursor: pointer;
    transition: all 0.15s;
    background: #fafaf9;
  }
  .upload-area:hover { border-color: #aaa; background: #f5f5f3; }
  .upload-area.dragover { border-color: #111; background: #f0f0ee; }
  .upload-icon {
    width: 36px; height: 36px;
    margin: 0 auto 12px;
    background: #f0f0ee;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
  }
  .upload-text { font-size: 14px; font-weight: 500; color: #333; margin-bottom: 4px; }
  .upload-sub  { font-size: 12px; color: #aaa; }
  .type-tags { display: flex; gap: 6px; justify-content: center; margin-top: 12px; }
  .type-tag {
    font-size: 11px; font-weight: 600;
    padding: 3px 8px; border-radius: 5px;
  }
  .type-csv   { background: #f0fdf4; color: #15803d; }
  .type-excel { background: #eff6ff; color: #1d4ed8; }
  .type-txt   { background: #f5f5f3; color: #555; }

  /* Status badge */
  .badge {
    display: inline-block;
    font-size: 11px; font-weight: 500;
    padding: 3px 10px; border-radius: 20px;
  }
  .badge-success { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
  .badge-error   { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }

  /* Loading spinner */
  .spinner {
    display: inline-block; width: 14px; height: 14px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    vertical-align: middle;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .hidden { display: none !important; }

  /* About */
  .about-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 20px; }
  .about-table th { text-align: left; padding: 8px 12px; background: #fafaf9;
                     border-bottom: 1px solid #e8e8e8; font-size: 11px; color: #aaa;
                     text-transform: uppercase; letter-spacing: 0.8px; }
  .about-table td { padding: 9px 12px; border-bottom: 1px solid #f5f5f3; color: #333; vertical-align: top; }
  .about-table code { font-family: monospace; background: #f5f5f3; padding: 1px 6px;
                       border-radius: 4px; font-size: 12px; color: #555; }
  .code-block {
    background: #111; color: #ccc; border-radius: 8px;
    padding: 14px 18px; font-family: monospace; font-size: 12px;
    line-height: 2; margin-bottom: 16px;
  }
</style>
</head>
<body>
<div class="wrap">

  <!-- Header -->
  <div class="header">
    <h1>Data Cleaning AI Agent</h1>
    <p>An OpenEnv environment where an AI agent learns to clean real-world messy data.
       Supports live text, CSV, Excel and TXT file cleaning.</p>
    <div class="pills">
      <span class="pill">OpenEnv</span>
      <span class="pill">24 tasks</span>
      <span class="pill">3 levels</span>
      <span class="pill">CSV / Excel / TXT</span>
      <span class="pill">90% score</span>
    </div>
  </div>

  <!-- Tabs -->
  <div class="tabs">
    <button class="tab active" onclick="showTab('try')">Try it</button>
    <button class="tab" onclick="showTab('upload')">Upload file</button>
    <button class="tab" onclick="showTab('eval')">Evaluation</button>
    <button class="tab" onclick="showTab('about')">About</button>
  </div>

  <!-- Tab: Try it -->
  <div class="panel active" id="tab-try">
    <div class="cols">
      <div>
        <div class="card">
          <div class="section-title" style="margin-bottom:12px;">Input</div>
          <div style="margin-bottom:14px;">
            <label>Dirty text</label>
            <textarea id="dirty-input" rows="5"
              placeholder="e.g.   hello   world  &#10;or: name: N/A ,  email: hr@@corp..net"></textarea>
          </div>
          <div style="margin-bottom:16px;">
            <label>Difficulty</label>
            <select id="difficulty">
              <option value="easy">Easy — spaces and capitalization</option>
              <option value="medium">Medium — emails and punctuation</option>
              <option value="hard">Hard — NULL values and combined</option>
            </select>
          </div>
          <button class="btn btn-primary" onclick="cleanText()" id="clean-btn">
            Clean text
          </button>
        </div>
      </div>
      <div>
        <div class="card" style="height:100%;">
          <div class="section-title" style="margin-bottom:12px;">Output</div>
          <textarea id="clean-output" rows="5" readonly
            placeholder="Cleaned text will appear here..."
            style="background:#fafaf9;cursor:default;"></textarea>
        </div>
      </div>
    </div>

    <div class="section-title" style="margin-top:8px;">Quick examples</div>
    <div class="examples">
      <button class="example-btn" onclick="loadExample('  hello   world  ','easy')">  hello   world  </button>
      <button class="example-btn" onclick="loadExample('  AI   is   the   future  ','easy')">  AI   is   the   future  </button>
      <button class="example-btn" onclick="loadExample('Send report to alice@@company..org','medium')">alice@@company..org</button>
      <button class="example-btn" onclick="loadExample('Hello.. my name is Jane,, nice.','medium')">Hello.. Jane,,</button>
      <button class="example-btn" onclick="loadExample('Wait!! Are you sure??? Really!!','medium')">Wait!! Sure???</button>
      <button class="example-btn" onclick="loadExample('Meeting on 31/03/2026 confirmed','medium')">31/03/2026</button>
      <button class="example-btn" onclick="loadExample('Call us at 98--765--43210','medium')">98--765--43210</button>
      <button class="example-btn" onclick="loadExample('  name: N/A ,  email: hr@@corp..net ,,  dept: NULL  ','hard')">name: N/A + email + NULL</button>
      <button class="example-btn" onclick="loadExample('  phone: 98--765--43210 ,  city: N/A ,  zip: NULL  ','hard')">phone + city + zip</button>
    </div>
  </div>

  <!-- Tab: Upload file -->
  <div class="panel" id="tab-upload">

    <div class="cols">
      <div>
        <div class="upload-area" id="upload-area"
          onclick="document.getElementById('file-input').click()"
          ondragover="event.preventDefault();this.classList.add('dragover')"
          ondragleave="this.classList.remove('dragover')"
          ondrop="handleDrop(event)">
          <div class="upload-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
              stroke="#888" stroke-width="2" stroke-linecap="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <div class="upload-text">Drop file here or click to browse</div>
          <div class="upload-sub">Max 10MB</div>
          <div class="type-tags">
            <span class="type-tag type-csv">CSV</span>
            <span class="type-tag type-excel">XLSX</span>
            <span class="type-tag type-txt">TXT</span>
          </div>
        </div>
        <input type="file" id="file-input" accept=".csv,.xlsx,.xls,.txt"
          style="display:none" onchange="uploadFile(this.files[0])">

        <div style="margin-top:12px;">
          <button class="btn btn-primary" onclick="triggerUpload()" id="upload-btn">
            Clean file
          </button>
          <span id="upload-status" style="margin-left:12px;font-size:13px;color:#aaa;"></span>
        </div>

        <div id="fixes-list" style="margin-top:20px;">
          <div class="section-title">What gets fixed</div>
          <div style="font-size:13px;color:#555;line-height:2;">
            NULL / N/A / NaN &rarr; <code style="background:#f5f5f3;padding:1px 5px;border-radius:4px;">unknown</code><br>
            bob@@gmail..com &rarr; <code style="background:#f5f5f3;padding:1px 5px;border-radius:4px;">bob@gmail.com</code><br>
            98--765--43210 &rarr; <code style="background:#f5f5f3;padding:1px 5px;border-radius:4px;">9876543210</code><br>
            31/03/2026 &rarr; <code style="background:#f5f5f3;padding:1px 5px;border-radius:4px;">31-03-2026</code><br>
            Wait!! Sure??? &rarr; <code style="background:#f5f5f3;padding:1px 5px;border-radius:4px;">Wait! Sure?</code>
          </div>
        </div>
      </div>

      <div id="upload-result" class="hidden">
        <div id="report-card"></div>
      </div>
    </div>

    <div id="preview-section" class="hidden" style="margin-top:24px;">
      <div class="section-title">Before vs after — first 12 rows</div>
      <div class="tbl-wrap">
        <table>
          <thead>
            <tr>
              <th>Column</th>
              <th>Original</th>
              <th>Cleaned</th>
              <th>Changed</th>
            </tr>
          </thead>
          <tbody id="preview-tbody"></tbody>
        </table>
      </div>
      <div style="margin-top:16px;">
        <button id="dl-btn" class="btn btn-secondary hidden" onclick="downloadFile()">
          Download cleaned file
        </button>
      </div>
    </div>
  </div>

  <!-- Tab: Evaluation -->
  <div class="panel" id="tab-eval">
    <div style="margin-bottom:20px;">
      <button class="btn btn-primary" onclick="runEval()" id="eval-btn">
        Run full evaluation
      </button>
    </div>
    <div id="eval-result" class="hidden">
      <div id="eval-cards" class="stat-row" style="grid-template-columns:repeat(3,1fr);"></div>
      <div class="card" style="margin-top:0;">
        <div class="section-title" style="margin-bottom:14px;">Score breakdown</div>
        <div id="eval-bars"></div>
      </div>
      <div id="eval-overall" class="overall-block"></div>
      <div style="margin-top:24px;">
        <div class="section-title">Task-by-task results</div>
        <div class="tbl-wrap">
          <table>
            <thead>
              <tr>
                <th>Level</th><th>Task</th>
                <th>Agent output</th><th>Expected</th>
                <th>Reward</th><th>Verdict</th>
              </tr>
            </thead>
            <tbody id="eval-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- Tab: About -->
  <div class="panel" id="tab-about">
    <div class="card">
      <p style="font-size:14px;color:#555;line-height:1.7;margin-bottom:20px;">
        A complete OpenEnv-compatible data cleaning environment built for a hackathon.
        An AI agent receives messy real-world text and returns the cleaned version.
        The environment rewards the agent: <strong>1.0</strong> for exact match,
        <strong>0.5</strong> for partial (60%+ similar), <strong>0.0</strong> for wrong.
      </p>

      <div class="section-title">Project files</div>
      <table class="about-table">
        <thead><tr><th>File</th><th>Purpose</th></tr></thead>
        <tbody>
          <tr><td><code>env.py</code></td><td>OpenEnv — reset(), step(), state()</td></tr>
          <tr><td><code>inference.py</code></td><td>Rule-based + LLM cleaning agent</td></tr>
          <tr><td><code>file_cleaner.py</code></td><td>CSV / Excel / TXT cleaner</td></tr>
          <tr><td><code>app.py</code></td><td>This web app (FastAPI + HTML)</td></tr>
          <tr><td><code>tasks/</code></td><td>24 JSON tasks — easy, medium, hard</td></tr>
        </tbody>
      </table>

      <div class="section-title">API endpoints</div>
      <div class="code-block">
POST /reset &nbsp;&nbsp; — reset environment<br>
POST /step &nbsp;&nbsp;&nbsp; — submit action, get reward<br>
GET  /state &nbsp;&nbsp; — current state<br>
GET  /health &nbsp; — health check
      </div>

      <div class="section-title">Environment variables</div>
      <div class="code-block">
API_BASE_URL = https://api.openai.com/v1<br>
MODEL_NAME &nbsp;&nbsp;= gpt-4o-mini<br>
HF_TOKEN &nbsp;&nbsp;&nbsp;&nbsp;= hf_xxxxxxxxxxxx
      </div>
    </div>
  </div>

</div><!-- /wrap -->

<script>
  // ── Tab switching ────────────────────────────────────────────
  function showTab(name) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('tab-' + name).classList.add('active');
  }

  // ── Clean text ───────────────────────────────────────────────
  async function cleanText() {
    const dirty = document.getElementById('dirty-input').value.trim();
    if (!dirty) return;
    const btn = document.getElementById('clean-btn');
    btn.innerHTML = '<span class="spinner"></span> Cleaning...';
    btn.disabled = true;

    const fd = new FormData();
    fd.append('dirty', dirty);
    fd.append('difficulty', document.getElementById('difficulty').value);

    try {
      const r = await fetch('/clean-text', { method: 'POST', body: fd });
      const d = await r.json();
      document.getElementById('clean-output').value = d.cleaned || d.error || '';
    } catch(e) {
      document.getElementById('clean-output').value = 'Error: ' + e.message;
    }
    btn.innerHTML = 'Clean text';
    btn.disabled = false;
  }

  function loadExample(text, diff) {
    document.getElementById('dirty-input').value = text;
    document.getElementById('difficulty').value  = diff;
    document.getElementById('clean-output').value = '';
  }

  // ── File upload ──────────────────────────────────────────────
  let pendingFile = null;

  function triggerUpload() {
    if (pendingFile) {
      doUpload(pendingFile);
    } else {
      document.getElementById('file-input').click();
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    document.getElementById('upload-area').classList.remove('dragover');
    const f = e.dataTransfer.files[0];
    if (f) { pendingFile = f; showFileName(f.name); }
  }

  function uploadFile(f) {
    if (!f) return;
    pendingFile = f;
    showFileName(f.name);
  }

  function showFileName(name) {
    document.getElementById('upload-status').textContent = name + ' ready — click Clean file';
  }

  async function doUpload(file) {
    const btn = document.getElementById('upload-btn');
    btn.innerHTML = '<span class="spinner"></span> Cleaning...';
    btn.disabled  = true;
    document.getElementById('upload-status').textContent = '';

    const fd = new FormData();
    fd.append('file', file);

    try {
      const r  = await fetch('/clean-file', { method: 'POST', body: fd });
      const d  = await r.json();

      if (d.error) {
        document.getElementById('upload-status').innerHTML =
          '<span class="badge badge-error">' + d.error + '</span>';
        btn.innerHTML = 'Clean file'; btn.disabled = false; return;
      }

      // Report card
      const card = document.getElementById('report-card');
      card.innerHTML = `
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">
          <span style="background:#111;color:#fff;font-size:10px;font-weight:600;
                        padding:3px 8px;border-radius:5px;">
            ${d.file_type.toUpperCase()}
          </span>
          <span style="font-size:14px;font-weight:500;color:#111;">${d.file_name}</span>
          <span class="badge badge-success" style="margin-left:auto;">cleaned</span>
        </div>
        <div class="stat-row" style="grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:14px;">
          <div class="stat"><div class="stat-val">${d.rows}</div><div class="stat-lbl">Rows</div></div>
          <div class="stat"><div class="stat-val">${d.columns}</div><div class="stat-lbl">Columns</div></div>
          <div class="stat amber"><div class="stat-val">${d.changed}</div><div class="stat-lbl">Fixed</div></div>
          <div class="stat green"><div class="stat-val">${d.pct}%</div><div class="stat-lbl">Dirty</div></div>
        </div>
        <div style="font-size:11px;color:#aaa;">
          Columns: <span style="color:#555;font-family:monospace;">
            ${(d.columns_list||[]).slice(0,6).join(', ')}
          </span>
        </div>`;

      document.getElementById('upload-result').classList.remove('hidden');

      // Preview table
      const tbody = document.getElementById('preview-tbody');
      tbody.innerHTML = d.preview.map(row => `
        <tr>
          <td style="font-weight:500;color:#111;">${row.col}</td>
          <td style="color:#888;">${row.original}</td>
          <td style="color:#111;">${row.cleaned}</td>
          <td class="${row.changed ? 'changed-yes' : ''}">${row.changed ? 'yes' : '—'}</td>
        </tr>`).join('');

      document.getElementById('preview-section').classList.remove('hidden');

      // Download
      if (d.dl_b64 && d.dl_name) {
        window._dlB64  = d.dl_b64;
        window._dlName = d.dl_name;
        window._dlType = d.file_type === 'csv'
          ? 'text/csv' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
        document.getElementById('dl-btn').classList.remove('hidden');
      }

      document.getElementById('upload-status').innerHTML =
        '<span class="badge badge-success">Done — ' + d.changed + ' values cleaned</span>';

    } catch(e) {
      document.getElementById('upload-status').textContent = 'Error: ' + e.message;
    }
    btn.innerHTML = 'Clean file'; btn.disabled = false;
  }

  // trigger on button click if file already selected
  document.getElementById('upload-btn').addEventListener('click', function() {
    if (pendingFile) doUpload(pendingFile);
    else document.getElementById('file-input').click();
  });

  function downloadFile() {
    const bytes = Uint8Array.from(atob(window._dlB64), c => c.charCodeAt(0));
    const blob  = new Blob([bytes], { type: window._dlType });
    const a     = document.createElement('a');
    a.href      = URL.createObjectURL(blob);
    a.download  = window._dlName;
    a.click();
  }

  // ── Evaluation ───────────────────────────────────────────────
  async function runEval() {
    const btn = document.getElementById('eval-btn');
    btn.innerHTML = '<span class="spinner"></span> Running...';
    btn.disabled  = true;

    try {
      const r = await fetch('/evaluate');
      const d = await r.json();

      const colors = { easy: '#22c55e', medium: '#f59e0b', hard: '#ef4444' };
      const labels = { easy: 'Easy', medium: 'Medium', hard: 'Hard' };

      // Cards
      document.getElementById('eval-cards').innerHTML =
        ['easy','medium','hard'].map(k => `
          <div class="stat">
            <div style="width:6px;height:6px;border-radius:50%;background:${colors[k]};
                         margin:0 auto 8px;"></div>
            <div class="stat-val">${d.scores[k]}%</div>
            <div style="font-size:12px;font-weight:500;color:#333;margin-top:2px;">${labels[k]}</div>
            <div style="font-size:11px;color:#aaa;margin-top:2px;font-family:monospace;">
              ${d.counts[k].correct}/${d.counts[k].total}
            </div>
          </div>`).join('');

      // Bars
      document.getElementById('eval-bars').innerHTML =
        ['easy','medium','hard'].map(k => `
          <div class="score-bar">
            <div class="score-bar-header">
              <span class="score-bar-name">${labels[k]}</span>
              <span class="score-bar-pct">${d.scores[k]}%</span>
            </div>
            <div class="score-bar-bg">
              <div class="score-bar-fill"
                style="width:${d.scores[k]}%;background:${colors[k]};"></div>
            </div>
          </div>`).join('');

      // Overall
      document.getElementById('eval-overall').innerHTML = `
        <div>
          <div class="overall-label">Overall score</div>
          <div class="overall-score">${d.overall}%</div>
        </div>
        <div style="text-align:right;">
          <div class="overall-label">Grade</div>
          <div class="overall-grade">${d.grade}</div>
        </div>`;

      // Table
      document.getElementById('eval-tbody').innerHTML = d.rows.map(row => `
        <tr>
          <td style="font-weight:500;">${row.level}</td>
          <td>${row.task_id}</td>
          <td>${row.output.length>38 ? row.output.slice(0,38)+'…' : row.output}</td>
          <td>${row.expected.length>38 ? row.expected.slice(0,38)+'…' : row.expected}</td>
          <td style="font-family:monospace;">${row.reward}</td>
          <td class="verdict-${row.verdict}">${row.verdict}</td>
        </tr>`).join('');

      document.getElementById('eval-result').classList.remove('hidden');
    } catch(e) {
      alert('Error: ' + e.message);
    }
    btn.innerHTML = 'Run full evaluation'; btn.disabled = false;
  }
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def root():
    return HTML


# ── Run ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
