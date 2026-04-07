"""
server/app.py - OpenEnv Server Entry Point
===========================================
Required by OpenEnv multi-mode deployment.
Has main() function and if __name__ == '__main__' block.
"""

import os
import sys
import json
import tempfile
import base64

# Add parent directory to path so we can import env, inference, file_cleaner
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from env import DataCleaningEnv
from inference import rule_based_clean
from file_cleaner import clean_uploaded_file

# ── App ────────────────────────────────────────────────────────
app = FastAPI(title="Data Cleaning OpenEnv", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_env = DataCleaningEnv(difficulty="easy")

class StepRequest(BaseModel):
    action: str

# ── OpenEnv endpoints ──────────────────────────────────────────

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

@app.post("/clean-text")
async def clean_text(dirty: str = Form(...), difficulty: str = Form("easy")):
    env = DataCleaningEnv(difficulty=difficulty)
    env.current_task = {"id": "demo", "input": dirty,
                        "expected_output": "", "description": "demo"}
    return JSONResponse(content={"cleaned": rule_based_clean(dirty)})

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
    dl_b64 = ""
    dl_name = ""
    if ftype == "csv" and result["csv_string"]:
        dl_b64  = base64.b64encode(result["csv_string"].encode()).decode()
        dl_name = file.filename.replace(".", "_cleaned.")
    elif ftype == "excel" and result.get("excel_bytes"):
        dl_b64  = base64.b64encode(result["excel_bytes"]).decode()
        dl_name = file.filename.replace(".", "_cleaned.")
    changed = report.get("cells_changed", report.get("lines_changed", 0))
    return JSONResponse(content={
        "file_type": ftype, "file_name": file.filename,
        "rows": report.get("rows", 0), "columns": report.get("columns", 1),
        "changed": changed, "pct": report.get("change_pct", 0),
        "columns_list": report.get("column_names", []),
        "preview": preview, "dl_b64": dl_b64, "dl_name": dl_name,
    })

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
                "level": d.upper(), "task_id": t["id"],
                "output": info["your_output"],
                "expected": info["expected_output"],
                "reward": rw,
                "verdict": "correct" if rw==1.0 else ("partial" if rw==0.5 else "wrong")
            })
        avg       = sum(rwds) / len(rwds)
        scores[d] = round(avg * 100)
        counts[d] = {
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

@app.get("/", response_class=HTMLResponse)
def root():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(root_dir, "app.py")
    # Extract HTML variable from root app.py
    import importlib.util
    spec = importlib.util.spec_from_file_location("root_app", app_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "HTML", "<h1>Data Cleaning AI Agent</h1>")


# ── main() — required by OpenEnv spec ─────────────────────────

def main():
    """
    Main function required by OpenEnv multi-mode deployment.
    Entry point: serve = 'server.app:main'
    """
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
