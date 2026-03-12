from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

# Define the agent with the Google Search tool
_search_agent = Agent(
    name="basic_search_agent",
    model="gemini-2.5-flash",
    description="Agent to answer questions using Google Search.",
    instruction="I can answer your questions by searching the internet. Just ask me anything!",
    tools=[google_search]
)

# Set up the runner and session service
_runner = Runner(
    app_name="simple_py_agent",
    agent=_search_agent,
    session_service=InMemorySessionService(),
    auto_create_session=True,
)


async def execute_search_query(query: str, session_id: str = "default_session") -> str:
    """Service method to handle the agent execution."""
    user_id = "default_user"

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=query)],
    )

    final_text: str | None = None

    async for event in _runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        # We only care about the final response event with text content.
        if getattr(event, "is_final_response", None) and event.is_final_response():
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                # Take the first text part as the main answer.
                part = event.content.parts[0]
                text = getattr(part, "text", None)
                if text:
                    final_text = text

    return final_text or "No response text produced by agent."