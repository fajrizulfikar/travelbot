from app.core.models import SearchResult

SYSTEM_PROMPT = """You are TravelBot AI, a helpful customer support assistant for a travel agency.
Answer ONLY using the provided context. Do not use any knowledge outside the context.
Respond with valid JSON matching this exact schema:
{
  "answer": "Your helpful answer here",
  "booking_link": null or "https://...",
  "related_services": ["service1", "service2"],
  "confidence": "high" or "medium" or "low",
  "escalate": false
}
Set confidence based on how well the context answers the question:
- "high": context directly answers the question
- "medium": context partially answers
- "low": context is insufficient or unrelated
Set booking_link to null if no booking URL is present in the context.
Limit related_services to max 3 items.
Return ONLY the JSON object, no other text."""


def build_prompt(message: str, chunks: list[SearchResult]) -> tuple[str, str]:
    if not chunks:
        user_prompt = (
            "No context found.\n\n"
            f"Question: {message}\n\n"
            "Respond that you cannot answer this question and set confidence to low."
        )
        return SYSTEM_PROMPT, user_prompt

    # Build context, trim if too long
    context_parts = []
    total_len = 0
    for i, result in enumerate(chunks):
        part = f"[{i+1}] {result.chunk.text}"
        total_len += len(part)
        if total_len > 12000:  # ~3000 tokens
            break
        context_parts.append(part)

    context = "\n\n".join(context_parts)
    user_prompt = f"Context:\n{context}\n\nQuestion: {message}"
    return SYSTEM_PROMPT, user_prompt
