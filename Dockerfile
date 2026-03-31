# ─────────────────────────────────────────────────────────────
# Dockerfile — Data Cleaning OpenEnv Environment
# ─────────────────────────────────────────────────────────────
# Builds a lightweight container that runs the inference script.
# Usage:
#   docker build -t data-cleaning-env .
#   docker run data-cleaning-env
# ─────────────────────────────────────────────────────────────

# Use official slim Python image for a small footprint
FROM python:3.10-slim

# Set a clean working directory inside the container
WORKDIR /app

# Copy dependency list first (Docker caches this layer)
COPY requirements.txt .

# Install dependencies (pyyaml only)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . .

# Make sure the tasks directory is present
# (it should be copied by the line above, but just in case)
RUN ls tasks/

# Default command: run the agent inference script
CMD ["python", "inference.py"]
