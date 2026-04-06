# 🧹 Data Cleaning AI Agent

> An OpenEnv-compatible environment where an AI agent learns to clean real-world messy data.
> Supports live text cleaning, CSV / Excel / TXT file upload, and full agent evaluation.

---

## 📌 What This Project Does

This project simulates a **real-world data cleaning task** as an OpenEnv environment.
An AI agent receives dirty / messy text and must return the cleaned version.
The environment rewards the agent based on how accurate its output is.

**6 types of errors handled automatically:**
- `NULL` / `N/A` / `NaN` / `none` → replaced with `unknown`
- Broken emails like `bob@@gmail..com` → `bob@gmail.com`
- Phone numbers like `98--765--43210` → `9876543210`
- Date formats like `31/03/2026` → `31-03-2026`
- Duplicate punctuation `!!` `??` `,,` → `!` `?` `,`
- Extra whitespace and spacing issues

---

## 🖥️ Live Demo

**Hugging Face Space:** [https://huggingface.co/spaces/KuldipD/data-cleaning-env](https://huggingface.co/spaces/KuldipD/data-cleaning-env)

---

## 📸 Screenshots

### Try it — live text cleaning
![output_1](https://github.com/user-attachments/assets/f5ae16c0-610f-4ced-bf42-bf0b6f35197c)


### Upload file — CSV / Excel / TXT cleaning
![output_2](https://github.com/user-attachments/assets/f8381bee-fdf6-42d0-899b-ad3c367dfe23)

### Before vs after — row-by-row preview
![output_3](https://github.com/user-attachments/assets/7af226c5-a2e8-4fe0-8ee7-e693aa074d8c)


### Full evaluation — agent benchmark
![output_4](https://github.com/user-attachments/assets/bf942ec9-6aaf-4afe-a40d-102b7b90abf4)


### About — API docs and project info
![output_5](https://github.com/user-attachments/assets/ba674446-7ce2-459a-9d73-8286224eb3bb)

---

## 📊 Agent Performance

| Level | Score | Tasks |
|-------|-------|-------|
| Easy | 100% | 8/8 correct |
| Medium | 81% | 5/8 correct |
| Hard | 88% | 6/8 correct |
| **Overall** | **90% — Grade A** | **19/24 correct** |

---

## 📁 Project Structure

```
data-cleaning-env/
│
├── app.py              ← FastAPI web app (HTML UI + API endpoints)
├── env.py              ← Core OpenEnv environment (reset, step, state)
├── inference.py        ← Rule-based + LLM cleaning agent
├── file_cleaner.py     ← CSV / Excel / TXT file cleaning module
│
├── tasks/
│   ├── easy.json       ← 8 easy tasks (spaces, capitalization)
│   ├── medium.json     ← 8 medium tasks (emails, punctuation, dates)
│   └── hard.json       ← 8 hard tasks (NULL values, combined errors)
│
├── openenv.yaml        ← OpenEnv environment definition
├── Dockerfile          ← Container definition
├── requirements.txt    ← Python dependencies
└── README.md           ← This file
```

---

## 🧠 How the Environment Works

```
Dirty Input → env.reset() → Agent reads state
           → Agent cleans text
           → env.step(cleaned_text)
           → Reward computed (0.0 / 0.5 / 1.0)
           → Score printed
```

### OpenEnv Interface

| Method | What it does |
|--------|-------------|
| `reset()` | Picks a random task, returns initial state |
| `step(action)` | Agent submits cleaned text → returns reward |
| `state()` | Returns current task info |

### Reward System

| Score | Condition |
|-------|-----------|
| **1.0** | Exact match with expected output |
| **0.5** | 60%+ similarity (partial credit) |
| **0.0** | Wrong answer |

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10 or higher
- pip

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/data-cleaning-env.git
cd data-cleaning-env
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your_token_here
```

### 4. Run the app

```bash
python app.py
```

Open your browser at `http://localhost:7860`

### 5. Run inference only

```bash
python inference.py --no-llm
```

---

## 🐳 Run with Docker

```bash
# Build
docker build -t data-cleaning-env .

# Run
docker run -p 7860:7860 \
  -e API_BASE_URL=https://api.openai.com/v1 \
  -e MODEL_NAME=gpt-4o-mini \
  -e HF_TOKEN=your_token_here \
  data-cleaning-env
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI |
| `POST` | `/reset` | Reset environment, returns initial state |
| `POST` | `/step` | Submit action, returns reward |
| `GET` | `/state` | Get current environment state |
| `GET` | `/health` | Health check — returns 200 |
| `POST` | `/clean-text` | Clean a text string |
| `POST` | `/clean-file` | Clean a CSV / Excel / TXT file |
| `GET` | `/evaluate` | Run full agent benchmark |

### Example — reset and step

```python
import requests

# Reset
state = requests.post("http://localhost:7860/reset",
                       params={"difficulty": "hard"}).json()
print(state["dirty_input"])

# Step
result = requests.post("http://localhost:7860/step",
                        json={"action": "your cleaned text"}).json()
print(result["reward"])
```

---

## 📋 Inference Log Format

The inference script emits structured JSON logs:

```json
{"event": "START", "task_id": "easy_1", "difficulty": "easy", "input": "  hello   world  "}
{"event": "STEP",  "task_id": "easy_1", "action": "Hello world", "reward": 1.0, "done": true}
{"event": "END",   "task_id": "easy_1", "final_reward": 1.0, "total_steps": 1}
{"event": "SUMMARY", "scores": {"easy": 1.0, "medium": 0.81, "hard": 0.88}, "overall": 0.90}
```

---

## ☁️ Deploy to Hugging Face Spaces

1. Go to [huggingface.co](https://huggingface.co) → New Space
2. Name: `data-cleaning-env` → SDK: **Docker** → Public
3. Upload all project files including `tasks/` folder
4. Go to **Settings → Variables and secrets** and add:

```
API_BASE_URL = https://api.openai.com/v1
MODEL_NAME   = gpt-4o-mini
HF_TOKEN     = hf_xxxxxxxxxxxx   ← add as Secret
```

5. Space builds automatically — live in 2-3 minutes

---

## 🔧 Environment Variables

| Variable | Type | Description |
|----------|------|-------------|
| `API_BASE_URL` | Variable | The API endpoint for the LLM |
| `MODEL_NAME` | Variable | The model identifier for inference |
| `HF_TOKEN` | **Secret** | Your Hugging Face API key |

---

## 📦 Requirements

```
fastapi
uvicorn
pydantic
openai
pandas
openpyxl
pyyaml
python-multipart
```

---

## 📄 License

MIT License — free to use, modify, and distribute.
