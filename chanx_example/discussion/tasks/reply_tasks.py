from typing import Any, cast

from channels.layers import get_channel_layer

from discussion.messages.common_messages import VotePayload, VoteUpdateEvent
from discussion.messages.topic_detail_messages import (
    NewReplyEvent,
    NewReplyEventPayload,
)
from discussion.models import DiscussionReply
from discussion.serializers.reply_serializers import DiscussionReplySerializer

channel_layer = get_channel_layer()


def task_broadcast_new_reply(reply_id: int) -> None:
    """
    Broadcast a new reply creation to connected users.

    Args:
        reply_id: ID of the newly created reply
    """
    try:
        reply = DiscussionReply.objects.select_related("author", "topic").get(
            id=reply_id
        )

        if not channel_layer:
            return

        # Serialize the reply
        serializer = DiscussionReplySerializer(reply)
        reply_data = cast(dict[str, Any], serializer.data)

        # Create the proper Pydantic payload
        payload = NewReplyEventPayload(
            id=reply.pk,
            content=reply.content,
            author=reply_data["author"],
            vote_count=reply.vote_count,
            is_accepted=reply.is_accepted,
            created_at=reply.created_at.isoformat(),
            formatted_created_at=reply_data["formatted_created_at"],
            topic_id=reply.topic.pk,
            topic_title=reply.topic.title,
        )

        # Import here to avoid circular imports
        from discussion.consumers.topic_consumer import DiscussionTopicConsumer

        # Send to the topic-specific group
        topic_group = f"discussion_topic_{reply.topic.pk}"
        DiscussionTopicConsumer.send_channel_event(
            topic_group, NewReplyEvent(payload=payload)
        )

    except DiscussionReply.DoesNotExist:
        pass


def task_broadcast_vote_update(
    target_type: str, target_id: int, vote_count: int
) -> None:
    """
    Broadcast vote updates for replies to all connected users.

    Args:
        target_type: "reply" (topics handled by topic_tasks)
        target_id: ID of the voted reply
        vote_count: Current vote count
    """
    try:
        if not channel_layer or target_type != "reply":
            return

        # Create the proper Pydantic payload
        payload = VotePayload(
            target_type=target_type,  # type: ignore[arg-type]
            target_id=target_id,
            vote_count=vote_count,
        )

        # Import here to avoid circular imports
        from discussion.consumers.topic_consumer import DiscussionTopicConsumer

        try:
            reply = DiscussionReply.objects.select_related("topic").get(id=target_id)
            topic_group = f"discussion_topic_{reply.topic.pk}"
            DiscussionTopicConsumer.send_channel_event(
                topic_group, VoteUpdateEvent(payload=payload)
            )
        except DiscussionReply.DoesNotExist:
            pass

    except Exception:
        pass
