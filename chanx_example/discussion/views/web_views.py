from typing import Any, cast

from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from rest_framework.permissions import AllowAny
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from discussion.models import DiscussionTopic
from discussion.serializers.topic_serializers import CreateDiscussionTopicSerializer
from discussion.tasks.topic_tasks import task_broadcast_new_topic
from utils.request import AuthenticatedRequest


class DiscussionHomeView(APIView):
    """Home page view for discussions with topic list."""

    renderer_classes = [TemplateHTMLRenderer]
    template_name = "discussion/home.html"
    permission_classes = [AllowAny]

    def get(self, request: HttpRequest) -> Response:
        """Handle GET requests to display the discussion home page."""
        # Initialize context
        context: dict[str, Any] = {
            "recent_topics": [],
        }

        # Get recent topics for display only if user is authenticated
        if request.user.is_authenticated:
            recent_topics = (
                DiscussionTopic.objects.select_related("author")
                .prefetch_related("replies")
                .order_by("-created_at")[:20]
            )
            context["recent_topics"] = recent_topics

        return Response(context)


class NewDiscussionTopicView(APIView):
    """View for creating new discussion topics."""

    renderer_classes = [TemplateHTMLRenderer]
    template_name = "discussion/new_topic.html"
    permission_classes = [AllowAny]  # Changed from IsAuthenticated to AllowAny

    def get(self, request: HttpRequest) -> Response:
        """Handle GET requests to display the new topic form."""
        return Response({})

    def post(self, request: Request) -> HttpResponse:
        """Handle POST requests to create a new topic."""
        # Check if user is authenticated for POST operations
        if not request.user.is_authenticated:
            # Redirect to login with next parameter
            login_url = reverse("rest_login")
            next_url = request.path
            return redirect(f"{login_url}?next={next_url}")

        request_auth = cast(AuthenticatedRequest, request)

        serializer = CreateDiscussionTopicSerializer(data=request.data)
        if serializer.is_valid():
            # Create the topic
            topic = serializer.save(author=request_auth.user)

            # Broadcast the new topic
            task_broadcast_new_topic(topic.pk)

            # Redirect to the new topic
            return redirect("discussion-detail", pk=topic.pk)

        # If serializer is invalid, re-render with errors
        return Response(
            {"errors": serializer.errors}, template_name=self.template_name, status=400
        )


class DiscussionTopicDetailView(APIView):
    """Detail view for a specific discussion topic."""

    renderer_classes = [TemplateHTMLRenderer]
    template_name = "discussion/topic_detail.html"
    permission_classes = [AllowAny]

    def get(self, request: HttpRequest, pk: int) -> Response:
        """Handle GET requests to display topic details."""
        topic = get_object_or_404(
            DiscussionTopic.objects.select_related(
                "author", "accepted_answer__author"
            ).prefetch_related("replies__author"),
            pk=pk,
        )

        # Increment view count
        DiscussionTopic.objects.filter(pk=pk).update(
            view_count=models.F("view_count") + 1
        )

        # Get all replies, ordered by votes then creation date
        replies = topic.replies.order_by("-vote_count", "created_at")

        return Response(
            {
                "topic": topic,
                "replies": replies,
            }
        )
