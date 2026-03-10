from abc import ABC, abstractmethod

class BaseCollector(ABC):
    @abstractmethod
    def fetch(self):
        """Fetch new items. Return list of dicts with keys: title, url, published_at, snippet"""
        raise NotImplementedError

class BaseDeliverer(ABC):
    @abstractmethod
    def deliver(self, summary_text, items):
        """Deliver the summary. items is the list of source items."""
        raise NotImplementedError
