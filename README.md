# simple-py-agent
This repo contains simple code to run an agentic system and demonstrate how agents are implemented in python.

# commands to bring up the server
uv sync
set -a; source app/.env; set +a
uv run python main.py

# swagger to test api
http://localhost:8000/docs
