from typing import Any, cast

from channels.layers import get_channel_layer

from discussion.messages.common_messages import VotePayload, VoteUpdateEvent
from discussion.messages.topic_detail_messages import (
    AnswerAcceptedEvent,
    AnswerAcceptedEventPayload,
    AnswerUnacceptedEvent,
    AnswerUnacceptedEventPayload,
)
from discussion.messages.topic_list_messages import (
    NewTopicEvent,
    NewTopicEventPayload,
)
from discussion.models import DiscussionReply, DiscussionTopic
from discussion.serializers.topic_serializers import DiscussionTopicListSerializer

channel_layer = get_channel_layer()


def task_broadcast_new_topic(topic_id: int) -> None:
    """
    Broadcast a new topic creation to all connected users.

    Args:
        topic_id: ID of the newly created topic
    """
    try:
        topic = DiscussionTopic.objects.select_related("author").get(id=topic_id)

        if not channel_layer:
            return

        # Serialize the topic
        serializer = DiscussionTopicListSerializer(topic)
        topic_data = cast(dict[str, Any], serializer.data)

        # Create the proper Pydantic payload
        payload = NewTopicEventPayload(
            id=topic.pk,
            title=topic.title,
            author=topic_data["author"],
            vote_count=topic.vote_count,
            reply_count=topic.reply_count,
            has_accepted_answer=topic.accepted_answer is not None,
            view_count=topic.view_count,
            created_at=topic.created_at.isoformat(),
            formatted_created_at=topic_data["formatted_created_at"],
        )

        # Import here to avoid circular imports
        from discussion.consumers.list_consumer import DiscussionListConsumer

        # Send to all discussion consumers via the list consumer
        DiscussionListConsumer.send_channel_event(
            "discussion_updates",  # Group name for all discussion updates
            NewTopicEvent(payload=payload),
        )

    except DiscussionTopic.DoesNotExist:
        pass


def task_broadcast_vote_update(
    target_type: str, target_id: int, vote_count: int
) -> None:
    """
    Broadcast vote updates to all connected users.

    Args:
        target_type: "topic" or "reply"
        target_id: ID of the voted item
        vote_count: Current vote count
    """
    try:
        if not channel_layer:
            return

        # Create the proper Pydantic payload
        payload = VotePayload(
            target_type=target_type,  # type: ignore[arg-type]
            target_id=target_id,
            vote_count=vote_count,
        )

        # Import here to avoid circular imports
        from discussion.consumers.topic_consumer import DiscussionTopicConsumer

        # Send to appropriate groups
        if target_type == "reply":
            try:
                reply = DiscussionReply.objects.select_related("topic").get(
                    id=target_id
                )
                topic_group = f"discussion_topic_{reply.topic.pk}"
                DiscussionTopicConsumer.send_channel_event(
                    topic_group, VoteUpdateEvent(payload=payload)
                )
            except DiscussionReply.DoesNotExist:
                pass
        elif target_type == "topic":
            # Send to topic-specific group
            topic_group = f"discussion_topic_{target_id}"
            DiscussionTopicConsumer.send_channel_event(
                topic_group, VoteUpdateEvent(payload=payload)
            )

    except Exception:
        pass


def task_broadcast_answer_accepted(topic_id: int, reply_id: int) -> None:
    """
    Broadcast answer acceptance to all connected users.

    Args:
        topic_id: ID of the topic
        reply_id: ID of the accepted reply
    """
    try:
        topic = DiscussionTopic.objects.select_related("author").get(id=topic_id)
        reply = DiscussionReply.objects.select_related("author").get(id=reply_id)

        if not channel_layer:
            return

        # Create the proper Pydantic payload
        payload = AnswerAcceptedEventPayload(
            topic_id=topic_id,
            topic_title=topic.title,
            reply_id=reply_id,
            reply_author=reply.author.email,
        )

        # Import here to avoid circular imports
        from discussion.consumers.topic_consumer import DiscussionTopicConsumer

        # Send to topic-specific group
        topic_group = f"discussion_topic_{topic_id}"
        DiscussionTopicConsumer.send_channel_event(
            topic_group, AnswerAcceptedEvent(payload=payload)
        )

    except (DiscussionTopic.DoesNotExist, DiscussionReply.DoesNotExist):
        pass


def task_broadcast_answer_unaccepted(topic_id: int, reply_id: int) -> None:
    """
    Broadcast answer unacceptance to all connected users.

    Args:
        topic_id: ID of the topic
        reply_id: ID of the reply that was unaccepted
    """
    try:
        topic = DiscussionTopic.objects.select_related("author").get(id=topic_id)
        reply = DiscussionReply.objects.select_related("author").get(id=reply_id)

        if not channel_layer:
            return

        # Create the proper Pydantic payload
        payload = AnswerUnacceptedEventPayload(
            topic_id=topic_id,
            topic_title=topic.title,
            reply_id=reply_id,
            reply_author=reply.author.email,
        )

        # Import here to avoid circular imports
        from discussion.consumers.topic_consumer import DiscussionTopicConsumer

        # Send to topic-specific group
        topic_group = f"discussion_topic_{topic_id}"
        DiscussionTopicConsumer.send_channel_event(
            topic_group, AnswerUnacceptedEvent(payload=payload)
        )

    except (DiscussionTopic.DoesNotExist, DiscussionReply.DoesNotExist):
        pass
