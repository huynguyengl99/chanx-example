from typing import Literal

from chanx.messages.base import BaseChannelEvent, BaseGroupMessage
from chanx.messages.incoming import PingMessage
from pydantic import BaseModel


# Common base payloads
class VotePayload(BaseModel):
    """Base payload for vote-related operations."""

    target_type: Literal["topic", "reply"]  # What we're voting on
    target_id: int  # ID of topic or reply
    vote_count: int  # Current vote count


# Common base messages
class VoteUpdatedMessage(BaseGroupMessage):
    """Broadcast when votes are updated."""

    action: Literal["vote_updated"] = "vote_updated"
    payload: VotePayload


# Common channel events
class VoteUpdateEvent(BaseChannelEvent):
    """Channel event for vote updates."""

    handler: Literal["handle_vote_update"] = "handle_vote_update"
    payload: VotePayload


# Union of messages that are common to both list and detail consumers
CommonIncomingMessage = PingMessage
