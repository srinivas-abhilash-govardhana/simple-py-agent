# simple-py-agent
This repository showcases a production-grade multi-agent orchestration framework designed to help with resume review and design preparation for targetted companies. Architected as a sequential Directed Acyclic Graph (DAG), the agentic system coordinates specialized autonomous agents (Sourcer, Strategist, InterviewArchitect) to execute complex reasoning chains. 

Sourcer agent takes user's query like "Give me preparation strategy for Staff Engineer at Uber and Stripe india with skills focused on Java, Python, Distributed Systems and AI Agents" and then searches the top open positions at the specified companies matching the level and skillset. This data is passed as context to Strategist agent which reviews the resume.md in classpath to suggest changes to resume. All of this data is passed to InterviewArchitect agent which acts as a Principal Engineer who analyse these jobs and resume to suggest some HLD, LLD and behavioral interview questions targeted at these companies at that level.

It demonstrates agentic tools, semantic gap analysis, and context-aware prompt engineering, transforming raw job targets into comprehensive, high-leverage interview strategies using external APIs and local context injection.

# This project uses Gemini LLM as brain and Google's SerpApi to scrape through jobs in google search. Create a new file called .env and add below Api keys for gemini and SerpApi.
GOOGLE_API_KEY=YOUR_GOOGLE_GEMINI_API_KEY
SERPAPI_KEY=YOUR_SERPAPI_KEY


# commands to bring up the local server
uv sync
set -a; source app/.env; set +a
uv run python main.py

# swagger to test api
http://localhost:8000/docs
