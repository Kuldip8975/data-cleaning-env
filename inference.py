"""
inference.py — Rule-Based AI Agent for Data Cleaning
=====================================================
This script:
  1. Loads the DataCleaningEnv environment
  2. Runs a simple rule-based AI agent on all difficulty levels
  3. Prints results and scores for each task

The agent applies a series of text-cleaning rules that simulate
what a real ML model would learn to do.
"""

import re
import json
import os
from env import DataCleaningEnv


# ──────────────────────────────────────────────────────────────────────────────
# Rule-Based Agent
# ──────────────────────────────────────────────────────────────────────────────

class RuleBasedAgent:
    """
    A simple rule-based cleaning agent.
    Applies a sequence of regex and string operations to clean dirty text.
    """

    def clean(self, dirty_text: str) -> str:
        """
        Apply all cleaning rules to the input text.

        Args:
            dirty_text (str): Raw / messy input.

        Returns:
            str: Cleaned output.
        """
        text = dirty_text

        # ── Step 1: Strip leading and trailing whitespace ──────────────────
        text = text.strip()

        # ── Step 2: Fix double @ in email addresses (e.g. bob@@mail.com) ──
        text = re.sub(r'@{2,}', '@', text)

        # ── Step 3: Fix double dots in email addresses (e.g. mail..com) ───
        #    Only inside what looks like an email address context
        text = re.sub(r'(?<=\w)\.{2,}(?=\w)', '.', text)

        # ── Step 4: Replace missing-value markers with "unknown" ───────────
        #    Handles: N/A, n/a, NULL, null, Null  (as whole words)
        text = re.sub(r'\bN/A\b', 'unknown', text, flags=re.IGNORECASE)
        text = re.sub(r'\bNULL\b', 'unknown', text, flags=re.IGNORECASE)

        # ── Step 5: Collapse duplicate punctuation ─────────────────────────
        #    e.g. "!!" → "!", "??" → "?", ",," → ","
        text = re.sub(r'([!?]){2,}', r'\1', text)
        text = re.sub(r',{2,}', ',', text)
        text = re.sub(r'\.{2,}', '.', text)

        # ── Step 6: Fix spacing around commas ─────────────────────────────
        #    "word ,  next" → "word, next"
        text = re.sub(r'\s*,\s*', ', ', text)

        # ── Step 7: Collapse multiple internal spaces to a single space ────
        text = re.sub(r' {2,}', ' ', text)

        # ── Step 8: Strip again after all replacements ─────────────────────
        text = text.strip()

        # ── Step 9: Capitalize first letter (easy-level requirement) ───────
        if text:
            text = text[0].upper() + text[1:]

        # ── Step 10: Remove trailing comma or space before end ─────────────
        text = text.rstrip(', ')

        return text


# ──────────────────────────────────────────────────────────────────────────────
# Evaluation Runner
# ──────────────────────────────────────────────────────────────────────────────

def run_evaluation(difficulty: str, agent: RuleBasedAgent, num_episodes: int = 5):
    """
    Run the agent on a given difficulty level and print results.

    Args:
        difficulty:    "easy", "medium", or "hard"
        agent:         The cleaning agent
        num_episodes:  How many tasks to run
    """
    print(f"\n{'='*60}")
    print(f"  DIFFICULTY: {difficulty.upper()}")
    print(f"{'='*60}")

    env = DataCleaningEnv(difficulty=difficulty)
    total_reward = 0.0

    for episode in range(1, num_episodes + 1):
        # Reset environment → get dirty input
        state = env.reset()
        dirty_input = state["dirty_input"]

        # Agent produces its cleaned output
        cleaned_output = agent.clean(dirty_input)

        # Submit to environment → get reward
        next_state, reward, done, info = env.step(cleaned_output)
        total_reward += reward

        # Pretty-print results
        print(f"\n  Episode {episode} — Task ID: {info['task_id']}")
        print(f"  Dirty Input    : {repr(dirty_input)}")
        print(f"  Agent Output   : {repr(cleaned_output)}")
        print(f"  Expected Output: {repr(info['expected_output'])}")
        verdict = "✅ CORRECT" if reward == 1.0 else ("⚠️  PARTIAL" if reward == 0.5 else "❌ WRONG")
        print(f"  Reward         : {reward}  {verdict}")

    avg_reward = total_reward / num_episodes
    print(f"\n  Average Reward for {difficulty.upper()}: {avg_reward:.2f} / 1.00")
    print(f"{'='*60}")
    return avg_reward


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "★"*60)
    print("   DATA CLEANING ENVIRONMENT — AGENT INFERENCE")
    print("★"*60)

    agent = RuleBasedAgent()
    results = {}

    for level in ["easy", "medium", "hard"]:
        avg = run_evaluation(level, agent, num_episodes=5)
        results[level] = avg

    print("\n" + "─"*60)
    print("  FINAL SUMMARY")
    print("─"*60)
    for level, avg in results.items():
        bar = "█" * int(avg * 20)
        print(f"  {level.upper():<8}: {avg:.2f}  [{bar:<20}]")

    overall = sum(results.values()) / len(results)
    print(f"\n  Overall Score: {overall:.2f} / 1.00")
    print("─"*60 + "\n")


if __name__ == "__main__":
    main()
