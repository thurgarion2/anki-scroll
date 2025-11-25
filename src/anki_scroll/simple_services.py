"""
Simple default implementation for all the services.
They can be replaced later by more complex implementations.
"""
from anki_scroll.services import Card, CardGenerator, Deck, DeckService

class SimpleDeck(Deck):
    """simple implementation of a deck"""
    # codex implement the deck


class SimpleCardGenerator(CardGenerator):
    """a simple gnerator that generate always the same card"""

    def __init__(
        self,
        card: Card,
    ) -> None:
        self._card = card

    def create_card(self, theme: str, instructions: str) -> Card:
        return self._card.model_copy()
    
class SimpleDeckService(DeckService):
    """
    Simple in-memory implementation of a deck service.
    The service do not support persitance.
    """
    pass
    # codex implement the deck