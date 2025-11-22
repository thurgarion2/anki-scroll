from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import Iterator, Optional


class Card(BaseModel):
    """anki card"""
    question: str
    answer: str
    

class Deck(ABC):
    
    @abstractmethod
    def add(self, card: Card):
        """add a card to the deck"""
        pass
    
    @abstractmethod
    def remove(self, card: Card):
        """remove the card from the deck"""
        pass
    
    @abstractmethod
    def __iter__(self) -> Iterator[Card]:
        pass

  
class CardGenerator(ABC):
    """api of service supporting carg generation from specification"""
    
    @abstractmethod
    def create_card(self, theme: str, instructions: str) -> Card:
        """
        params:
        theme -- the theme of the cards to generate
        instructions -- additonal instructions to follow when generting the card
        """
        pass
    

class SimpleDeck(Deck):
    """simple in memory implementation of a deck"""

    def __init__(self) -> None:
        self._cards: list[Card] = []

    def add(self, card: Card):
        # prevent storing the exact same card instance twice
        if any(existing is card for existing in self._cards):
            return
        self._cards.append(card)

    def remove(self, card: Card):
        try:
            self._cards.remove(card)
        except ValueError:
            pass

    def __iter__(self) -> Iterator[Card]:
        return iter(tuple(self._cards))
    
class SimpleCardGenerator(CardGenerator):
    """a simple gnerator that generate always the same card"""

    def __init__(
        self,
        card: Card,
    ) -> None:
        self._card = card

    def create_card(self, theme: str, instructions: str) -> Card:
        return self._card.model_copy()
