"""Transfer module for technology transfer conversation management."""

from paper_scraper.modules.transfer.models import (
    ConversationMessage,
    ConversationResource,
    MessageTemplate,
    StageChange,
    TransferConversation,
)
from paper_scraper.modules.transfer.router import router
from paper_scraper.modules.transfer.service import TransferService

__all__ = [
    "ConversationMessage",
    "ConversationResource",
    "MessageTemplate",
    "StageChange",
    "TransferConversation",
    "TransferService",
    "router",
]
