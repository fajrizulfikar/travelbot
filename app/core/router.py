import re
from app.models.chat import ChatResponse
from app.config import Settings

HUMAN_REQUEST_PATTERNS = [
    r"speak\s+to\s+(?:an?\s+)?agent",
    r"\bhuman\b",
    r"\brepresentative\b",
    r"talk\s+to\s+someone",
    r"need\s+help",
    r"contact\s+support",
    r"talk\s+to\s+(?:an?\s+)?agent",
]

ESCALATION_ANSWER = (
    "I'm connecting you to a human agent who can better assist you. "
    "Please hold on."
)


class RoutingEngine:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._patterns = [re.compile(p, re.IGNORECASE) for p in HUMAN_REQUEST_PATTERNS]

    def should_escalate(
        self,
        response: ChatResponse,
        max_score: float,
        message: str,
        formatter_used_fallback: bool,
    ) -> bool:
        if max_score < self._settings.CONFIDENCE_THRESHOLD:
            return True
        if response.confidence == "low":
            return True
        if any(p.search(message) for p in self._patterns):
            return True
        if formatter_used_fallback:
            return True
        return False

    def escalate_response(self, response: ChatResponse) -> ChatResponse:
        return response.model_copy(update={"escalate": True, "answer": ESCALATION_ANSWER})
