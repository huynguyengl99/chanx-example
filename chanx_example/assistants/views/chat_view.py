from django.http import HttpRequest
from rest_framework.permissions import AllowAny
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView


class AssistantChatView(APIView):
    """View for the assistant chat interface."""

    renderer_classes = [TemplateHTMLRenderer]
    template_name = "assistants/chat.html"
    permission_classes = [AllowAny]

    def get(self, request: HttpRequest) -> Response:
        """Handle GET requests to display the home page."""

        return Response({}, template_name=self.template_name)
