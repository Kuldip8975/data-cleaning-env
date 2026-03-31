# 🧹 Data Cleaning System — OpenEnv Environment

> A real-world AI environment where an agent learns to clean messy text data.
> Built for hackathons using the OpenEnv interface standard.

---

## 📌 What This Project Does

This project simulates a **real-world data cleaning task**.  
An AI agent receives dirty / messy text and must return the cleaned version.  
The environment rewards the agent based on how close its output is to the correct answer.

---

## 📁 Project Structure

```
data_cleaning_env/
│
├── env.py              ← Core OpenEnv environment (reset, step, state)
├── inference.py        ← Rule-based AI agent + evaluation runner
│
├── tasks/
│   ├── easy.json       ← 5 easy tasks (spaces, capitalization)
│   ├── medium.json     ← 5 medium tasks (emails, punctuation)
│   └── hard.json       ← 5 hard tasks (missing values, combined errors)
│
├── openenv.yaml        ← Environment definition file
├── Dockerfile          ← Container definition
├── requirements.txt    ← Python dependencies
└── README.md           ← This file
```

---

## 🧠 How the Environment Works

### Interface

| Method | What it does |
|--------|-------------|
| `reset()` | Picks a random task, returns initial state |
| `step(action)` | Agent submits cleaned text → returns `(state, reward, done, info)` |
| `state()` | Returns current task info (dirty input, description, etc.) |

### Reward System

| Score | Condition |
|-------|-----------|
| **1.0** | Agent output exactly matches expected output |
| **0.5** | Agent output is ≥ 60% similar (partial credit) |
| **0.0** | Agent output is wrong |

### Difficulty Levels

| Level | Tasks |
|-------|-------|
| **Easy** | Strip spaces, fix capitalization |
| **Medium** | Fix broken emails, duplicate punctuation |
| **Hard** | Replace missing values (N/A, NULL), combined errors |

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip

### 1. Clone / Download the project

```bash
git clone https://github.com/YOUR_USERNAME/data-cleaning-env.git
cd data-cleaning-env
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the agent

```bash
python inference.py
```

---

## 🖥️ Example Output

```
★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
   DATA CLEANING ENVIRONMENT — AGENT INFERENCE
★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

============================================================
  DIFFICULTY: EASY
============================================================

  Episode 1 — Task ID: easy_1
  Dirty Input    : '  hello   world  '
  Agent Output   : 'Hello world'
  Expected Output: 'Hello world'
  Reward         : 1.0  ✅ CORRECT

  Episode 2 — Task ID: easy_3
  Dirty Input    : '  my name is john doe  '
  Agent Output   : 'My name is john doe'
  Expected Output: 'My name is john doe'
  Reward         : 1.0  ✅ CORRECT

  ...

  Average Reward for EASY: 1.00 / 1.00

──────────────────────────────────────────────────────────────
  FINAL SUMMARY
──────────────────────────────────────────────────────────────
  EASY    : 1.00  [████████████████████]
  MEDIUM  : 0.90  [██████████████████  ]
  HARD    : 0.70  [██████████████      ]

  Overall Score: 0.87 / 1.00
──────────────────────────────────────────────────────────────
```

---

## 🐳 Run with Docker

### Build the image

```bash
docker build -t data-cleaning-env .
```

### Run the container

```bash
docker run data-cleaning-env
```

---

## ☁️ Deploy to Hugging Face Spaces

Follow these steps to deploy the project on [Hugging Face Spaces](https://huggingface.co/spaces):

### Step 1 — Create a Hugging Face account
Go to [huggingface.co](https://huggingface.co) and sign up for a free account.

### Step 2 — Create a new Space
1. Click your profile icon → **New Space**
2. Give it a name (e.g., `data-cleaning-env`)
3. Choose **Docker** as the SDK
4. Set visibility to **Public**
5. Click **Create Space**

### Step 3 — Upload your files
You can either:

**Option A — Use the web interface:**
1. Click **Files** tab in your Space
2. Click **Add file → Upload files**
3. Upload all project files including the `tasks/` folder

**Option B — Use Git:**
```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/data-cleaning-env
cd data-cleaning-env
# Copy all your project files here
git add .
git commit -m "Initial commit"
git push
```

### Step 4 — Add a Gradio UI (optional, for browser demo)

Install gradio:
```bash
pip install gradio
```

Create `app.py`:
```python
import gradio as gr
from env import DataCleaningEnv
from inference import RuleBasedAgent

agent = RuleBasedAgent()

def clean_text(dirty_input, difficulty):
    env = DataCleaningEnv(difficulty=difficulty)
    env.current_task = {"id": "demo", "input": dirty_input,
                        "expected_output": "", "description": "Live demo"}
    cleaned = agent.clean(dirty_input)
    return cleaned

demo = gr.Interface(
    fn=clean_text,
    inputs=[
        gr.Textbox(label="Dirty Input"),
        gr.Dropdown(["easy", "medium", "hard"], label="Difficulty")
    ],
    outputs=gr.Textbox(label="Cleaned Output"),
    title="Data Cleaning AI Agent"
)
demo.launch()
```

### Step 5 — Your Space is live!
Visit `https://huggingface.co/spaces/YOUR_USERNAME/data-cleaning-env`

---

## ✅ Hackathon Checklist

- [x] `env.py` with `reset()`, `step()`, `state()`
- [x] Reward system: 1.0 / 0.5 / 0.0
- [x] 3 difficulty levels: easy, medium, hard
- [x] Task JSON files with input + expected_output
- [x] Rule-based AI agent in `inference.py`
- [x] `openenv.yaml` environment definition
- [x] `Dockerfile` (fully working)
- [x] `requirements.txt`
- [x] `README.md` with full instructions
- [x] Hugging Face deployment guide

---

## 📄 License

MIT License — free to use, modify, and distribute.
