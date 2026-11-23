"""Agent chat endpoint."""
from fastapi import APIRouter

from app.agent.chat import run_agent_chat
from app.models import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/agent/chat", response_model=ChatResponse)
def agent_chat(body: ChatRequest) -> ChatResponse:
    """Send a message to the AI agent and get a response with policy decisions."""
    # Lazy import to avoid circular dependency with app.main
    from app.main import policy_engine

    return run_agent_chat(body.message, policy_engine)
