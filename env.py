"""
env.py — Data Cleaning OpenEnv Environment
==========================================
This file defines the DataCleaningEnv class, which simulates a real-world
data cleaning task for an AI agent.

The environment follows the OpenEnv interface:
  - reset()  → start a new episode with a fresh task
  - step(action) → agent submits a cleaned string; get reward + next state
  - state()  → return current task information
"""

import json
import os
import re
import random


class DataCleaningEnv:
    """
    OpenEnv-compatible environment for data cleaning tasks.

    The agent receives dirty text as input and must return clean text.
    Reward is based on similarity to the expected output.
    """

    # Paths to task JSON files (relative to this file)
    TASK_FILES = {
        "easy":   os.path.join(os.path.dirname(__file__), "tasks", "easy.json"),
        "medium": os.path.join(os.path.dirname(__file__), "tasks", "medium.json"),
        "hard":   os.path.join(os.path.dirname(__file__), "tasks", "hard.json"),
    }

    def __init__(self, difficulty: str = "easy"):
        """
        Initialize the environment.

        Args:
            difficulty: "easy", "medium", or "hard"
        """
        if difficulty not in self.TASK_FILES:
            raise ValueError(f"difficulty must be one of {list(self.TASK_FILES.keys())}")

        self.difficulty = difficulty
        self.tasks = self._load_tasks(difficulty)
        self.current_task = None
        self.done = False
        self.steps_taken = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_tasks(self, difficulty: str):
        """Load tasks from the JSON file for the given difficulty."""
        path = self.TASK_FILES[difficulty]
        with open(path, "r") as f:
            return json.load(f)

    def _compute_reward(self, predicted: str, expected: str) -> float:
        """
        Compute a reward between 0.0 and 1.0.

        Rules:
          1.0  → exact match (after stripping extra whitespace)
          0.5  → partial match (≥ 60% character-level similarity)
          0.0  → wrong answer
        """
        # Normalize both strings for fair comparison
        pred_clean = " ".join(predicted.strip().split())
        exp_clean  = " ".join(expected.strip().split())

        # Exact match
        if pred_clean == exp_clean:
            return 1.0

        # Partial match: compute character-level similarity ratio
        similarity = self._similarity_ratio(pred_clean, exp_clean)
        if similarity >= 0.6:
            return 0.5

        return 0.0

    @staticmethod
    def _similarity_ratio(a: str, b: str) -> float:
        """
        Simple character-level similarity ratio using longest common subsequence length.
        Returns a value between 0.0 and 1.0.
        """
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0

        # Count matching characters (order-insensitive approximation)
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a, b).ratio()

    # ------------------------------------------------------------------
    # OpenEnv Interface
    # ------------------------------------------------------------------

    def reset(self):
        """
        Start a new episode by picking a random task.

        Returns:
            dict: The current state (task information).
        """
        self.current_task = random.choice(self.tasks)
        self.done = False
        self.steps_taken = 0
        return self.state()

    def step(self, action: str):
        """
        The agent submits its cleaned text as an action.

        Args:
            action (str): The cleaned text produced by the agent.

        Returns:
            tuple: (next_state, reward, done, info)
                - next_state (dict): same task info (episode ends after 1 step)
                - reward (float): 0.0, 0.5, or 1.0
                - done (bool): True (each task is a single-step episode)
                - info (dict): extra details for debugging
        """
        if self.current_task is None:
            raise RuntimeError("Call reset() before step().")
        if self.done:
            raise RuntimeError("Episode is done. Call reset() to start a new one.")

        expected = self.current_task["expected_output"]
        reward   = self._compute_reward(action, expected)

        self.steps_taken += 1
        self.done = True   # single-step episode

        info = {
            "task_id":         self.current_task["id"],
            "difficulty":      self.difficulty,
            "your_output":     action,
            "expected_output": expected,
            "reward":          reward,
            "steps_taken":     self.steps_taken,
        }

        return self.state(), reward, self.done, info

    def state(self):
        """
        Return the current environment state.

        Returns:
            dict: Contains 'dirty_input', 'description', 'difficulty', 'done'.
        """
        if self.current_task is None:
            return {"dirty_input": None, "description": None,
                    "difficulty": self.difficulty, "done": True}

        return {
            "dirty_input":  self.current_task["input"],
            "description":  self.current_task["description"],
            "difficulty":   self.difficulty,
            "done":         self.done,
        }
