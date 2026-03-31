import gradio as gr
from env import DataCleaningEnv
from inference import RuleBasedAgent

agent = RuleBasedAgent()

def clean_text(dirty_input, difficulty):
    env = DataCleaningEnv(difficulty=difficulty)
    env.current_task = {
        "id": "demo",
        "input": dirty_input,
        "expected_output": "",
        "description": "Live demo"
    }
    cleaned = agent.clean(dirty_input)
    return cleaned

demo = gr.Interface(
    fn=clean_text,
    inputs=[
        gr.Textbox(label="✍️ Enter Dirty Text", 
                   placeholder="e.g.   hello   world  "),
        gr.Dropdown(
            ["easy", "medium", "hard"], 
            label="🎯 Difficulty Level",
            value="easy"
        )
    ],
    outputs=gr.Textbox(label="✅ Cleaned Output"),
    title="🧹 Data Cleaning AI Agent",
    description="Enter messy text and let the AI agent clean it!",
    examples=[
        ["  hello   world  ", "easy"],
        ["Send email to bob@@gmail..com", "medium"],
        ["name: N/A ,  email: hr@@corp..net", "hard"],
    ]
)

demo.launch()
