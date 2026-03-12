import os
import requests
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

# ==========================================
# 1. Define Custom ADK Tools
# ADK automatically parses the docstrings and type hints to figure out how to use these.
# ==========================================
def read_resume() -> str:
    """Reads the candidate's resume from the local file system to understand their background."""
    try:
        with open("resume.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback for testing if the file isn't created yet
        return "John Michael Sanders is a Staff Software Engineer with 15 years of experience. Strong background in backend systems, but needs to highlight staff-level scope."


def fetch_job_description(role: str, company: str) -> str:
    """Fetches the latest job description for a specific role and company."""
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        return "Error: SERPAPI_KEY not found in environment variables."

    params = {
        "engine": "google_jobs",
        "q": f"{role} at {company}",
        "api_key": api_key,
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params)
        response.raise_for_status()
        data = response.json()
        jobs = data.get("jobs_results", [])

        if not jobs:
            return f"No jobs found for {role} at {company}."

        # Return the top 3 jobs found to give the agent comprehensive context
        results = []
        for job in jobs[:3]:
            title = job.get("title", "N/A")
            description = job.get("description", "N/A")
            results.append(f"Title: {title}\nDescription: {description}")

        return "\n\n".join(results)

    except Exception as e:
        return f"Error fetching job description: {str(e)}"

# ==========================================
# 2. Define the Service & Orchestration
# ==========================================

class JobFunnelService:
    def __init__(self):
        # Initialize the LLM Engine (Gemini 2.5 Flash is the default for ADK)
        self.llm = "gemini-2.5-flash"

        # Agent 1: The Sourcer
        self.sourcer = Agent(
            name="Sourcer",
            model=self.llm,
            description="Extracts and summarizes technical job requirements.",
            instruction=(
                "You are a Staff-level technical recruiter. Use the fetch_job_description tool "
                "to get the JD, then extract the core skills,architecture and leadership requirements "
                "into a strict bulleted list."
            ),
            tools=[fetch_job_description]
        )

        # Agent 2: The Strategist
        self.strategist = Agent(
            name="Strategist",
            model=self.llm,
            description="Compares a candidate's resume to a job description.",
            instruction=(
                "You are an elite career coach. Use the read_resume tool to load the candidate's "
                "profile. Compare it against the provided job requirements. Output a highly specific "
                "list of 3 resume tweaks needed to pass the resume screen. Return the results in crisp bullet points which are easily human readable."
            ),
            tools=[read_resume]
        )

        # Agent 3: The Interview Architect
        self.architect = Agent(
            name="InterviewArchitect",
            model=self.llm,
            description="Generates highly specific technical interview prep.",
            instruction=(
                "You are a Principal Engineer conducting an interview. Based on the job description "
                "and the candidate's resume gaps, generate 1 High-Level Design (HLD) question and 1 Low-Level Design (LLD) questions and "
                "1 Behavioral question that are statistically likely to be asked in this loop. Return the results in crisp bullet points which are easily human readable."
            ),
            tools=[] # No tools needed, it relies purely on reasoning from the context passed to it
        )

    async def _execute_agent(self, runner: Runner, prompt: str) -> str:
        """Helper to execute agent and extract clean text response."""
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )

        final_text = ""

        async for event in runner.run_async(
            user_id="default_user",
            session_id="default_session",
            new_message=content,
        ):
            if getattr(event, "is_final_response", None) and event.is_final_response():
                if getattr(event, "content", None) and getattr(event.content, "parts", None):
                    part = event.content.parts[0]
                    text = getattr(part, "text", None)
                    if text:
                        final_text = text
        return final_text or "No response."

    def _clean_response_to_list(self, text: str) -> list[str]:
        """Converts text with newlines/bullets into a clean list of strings."""
        lines = text.split('\n')
        cleaned = []
        for line in lines:
            line = line.strip()
            if line:
                # Remove markdown bullet points if present at start
                cleaned.append(line.lstrip("*-•").strip())
        return cleaned

    async def generate_prep_strategy(self, query: str) -> dict:
        """
        The main orchestration pipeline. This acts as the DAG (Directed Acyclic Graph),
        passing the output of one agent directly into the prompt of the next.
        """

        # In Google ADK, Runners manage the session state and execution of an agent
        sourcer_runner = Runner(agent=self.sourcer, app_name="sourcer", session_service=InMemorySessionService(), auto_create_session=True)
        strategist_runner = Runner(agent=self.strategist, app_name="strategist", session_service=InMemorySessionService(), auto_create_session=True)
        architect_runner = Runner(agent=self.architect, app_name="architect", session_service=InMemorySessionService(), auto_create_session=True)

        print(f"Starting pipeline for user query: '{query}'...")

        # Step 1: Gather JD based on raw query
        print("Running Sourcer...")
        # We pass the raw query directly. The agent will read it, realize it needs
        # to call fetch_job_description (potentially multiple times for Uber and Stripe),
        # and summarize the results.
        jd_result = await self._execute_agent(
            sourcer_runner,
            f"Fulfill this user request: '{query}'. "
            "Extract the target roles, companies and location, fetch their job descriptions using your tool, and summarize the core requirements."
        )
        
        # Step 2: Gap Analysis
        print("Running Strategist...")
        gap_analysis = await self._execute_agent(
            strategist_runner,
            f"Here are the job requirements gathered: {jd_result}. "
            "Use your tool to read the resume and identify what's missing to secure these roles. Return the results in crisp bullet points which are easily human readable."
        )

        # Step 3: Interview Prep
        print("Running Interview Architect...")
        final_prep = await self._execute_agent(
            architect_runner,
            f"Generate HLD, LLD and behavioral prep based on the original request: '{query}'. "
            f"\nRequirements: {jd_result} \nResume Gaps: {gap_analysis}. Return the results in crisp bullet points which are easily human readable."
        )

        # Return the aggregated results
        return {
            "original_query": query,
            "resume_analysis": self._clean_response_to_list(gap_analysis),
            "interview_prep": self._clean_response_to_list(final_prep)
        }

# ==========================================
# 3. Expose Service Method
# ==========================================
_service = JobFunnelService()

async def generate_prep_strategy(query: str) -> dict:
    """Module-level wrapper to call the service instance."""
    return await _service.generate_prep_strategy(query)


