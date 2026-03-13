import hashlib
import json
import logging
from app.models.chat import ChatResponse

logger = logging.getLogger(__name__)

FALLBACK_RESPONSE = ChatResponse(
    answer="I'm sorry, I couldn't process that. Please try again or speak to an agent.",
    booking_link=None,
    related_services=[],
    confidence="low",
    escalate=True,
    session_id="",
)


class ResponseFormatter:
    def parse(self, raw_text: str, session_id: str) -> tuple[ChatResponse, bool]:
        """Returns (ChatResponse, used_fallback)."""
        try:
            text = raw_text.strip()
            # Strip markdown code fences
            if text.startswith("```"):
                lines = text.split("\n")
                # Remove first line (```json or ```) and last line (```)
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines)
            data = json.loads(text)
            # Clamp related_services to 3
            if "related_services" in data and isinstance(data["related_services"], list):
                data["related_services"] = data["related_services"][:3]
            # Fill defaults
            data.setdefault("booking_link", None)
            data.setdefault("related_services", [])
            data.setdefault("confidence", "low")
            data.setdefault("escalate", False)
            data.setdefault("answer", "")
            response = ChatResponse(**data, session_id=session_id)
            return response, False
        except Exception as exc:
            raw_hash = hashlib.md5(raw_text.encode()).hexdigest()[:8]
            logger.warning("Formatter parse failed (hash=%s): %s", raw_hash, exc)
            fallback = FALLBACK_RESPONSE.model_copy(update={"session_id": session_id})
            return fallback, True
