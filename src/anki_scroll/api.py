from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import Iterator


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
    
class SimpleCardGenerator(ABC):
    """a simple gnerator that generate always the same card"""

