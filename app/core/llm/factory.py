from app.core.llm.gateway import LLMGateway
from app.config import Settings


def get_llm_gateway(settings: Settings) -> LLMGateway:
    if settings.LLM_PROVIDER == "claude":
        from app.core.llm.claude_adapter import ClaudeAdapter
        return ClaudeAdapter(api_key=settings.CLAUDE_API_KEY, openai_api_key=settings.OPENAI_API_KEY)
    elif settings.LLM_PROVIDER == "openai":
        from app.core.llm.openai_adapter import OpenAIAdapter
        return OpenAIAdapter(api_key=settings.OPENAI_API_KEY)
    else:
        raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")
