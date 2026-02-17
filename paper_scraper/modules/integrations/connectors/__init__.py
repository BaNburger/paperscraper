"""Integration connector implementations."""

from paper_scraper.modules.integrations.connectors.market_feed import MarketFeedConnector
from paper_scraper.modules.integrations.connectors.zotero import (
    ZoteroConnector,
    ZoteroCredentials,
)

__all__ = ["MarketFeedConnector", "ZoteroConnector", "ZoteroCredentials"]
