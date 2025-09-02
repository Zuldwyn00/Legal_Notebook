"""
Domain-specific AI client agents.

These agents inherit from ChatClient and add specialized business logic
for specific tasks like metadata extraction, lead scoring, etc.
"""

from .summarization import SummarizationAgent
from .chat import ChatAgent

__all__ = [
    "SummarizationAgent",
    "ChatAgent",
]
