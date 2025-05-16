from typing import Any

from django.views.generic import TemplateView


class AssistantChatView(TemplateView):
    """View for the assistant chat interface."""

    template_name = "assistants/chat.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # Add any additional context if needed
        return context
