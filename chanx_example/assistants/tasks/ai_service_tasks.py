import logging
from textwrap import dedent

from assistants.constants import TRUNCATED_TITLE_LENGTH
from assistants.services.ai_service import OpenAIService

logger = logging.getLogger(__name__)


def task_generate_conversation_title(message: str) -> str:
    """
    Generate a title for a conversation based on the first message.

    Args:
        message: First user message in the conversation

    Returns:
        str: Generated title
    """
    # If the message is short enough, use it directly
    if len(message) <= TRUNCATED_TITLE_LENGTH:
        return message

    # For longer messages, try to generate a summary
    ai_service = OpenAIService(model="gpt-4o-mini", temperature=0.3)

    summary_prompt = dedent(
        f"""
    Generate a short, descriptive title (max 50 characters) for a conversation that starts with this message:

    "{message}"

    Title:"""
    )

    # Use invoke method to get a single response
    response = ai_service.llm.invoke(ai_service.format_messages(summary_prompt, []))

    # Extract content from the response - LangChain returns an AIMessage object
    if hasattr(response, "content") and isinstance(response.content, str):
        title = response.content.strip()
    else:
        # Fallback to truncation if AI generation fails
        title = message[:TRUNCATED_TITLE_LENGTH]
        if len(message) > TRUNCATED_TITLE_LENGTH:
            title += "..."
        return title

    # Ensure title is not empty
    if not title:
        title = message[:TRUNCATED_TITLE_LENGTH]
        if len(message) > TRUNCATED_TITLE_LENGTH:
            title += "..."
        return title

    # Truncate if too long
    if len(title) > TRUNCATED_TITLE_LENGTH:
        title = title[:47] + "..."

    return title
