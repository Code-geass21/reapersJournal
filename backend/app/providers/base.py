from abc import ABC, abstractmethod
from typing import Dict, List, Any

class PriceProvider(ABC):
    @abstractmethod
    def fetch_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Must return a dictionary keyed by symbol containing:
        { "price": float, "bid": float|None, "ask": float|None, "source": str }
        """
        pass

class NewsProvider(ABC):
    @abstractmethod
    def fetch_upcoming_news(self) -> List[Dict[str, Any]]:
        """
        Must return a list of dictionaries containing:
        { "title": str, "country": str, "impact": str, "time": str (ISO) }
        """
        pass
