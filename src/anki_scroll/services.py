from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import Iterator, Optional


class Card(BaseModel):
    """anki card"""
    question: str
    answer: str
    

class Deck(ABC):
    
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def id(self) -> str:
        """
        A hash of the name, uniquely identify the deck. 
        It implies two different deck cannot have the same name.
        """
        raise NotImplementedError
    
    @abstractmethod
    def add(self, card: Card):
        """add a card to the deck"""
        raise NotImplementedError
    
    @abstractmethod
    def remove(self, card: Card):
        """remove the card from the deck"""
        raise NotImplementedError
    
    @abstractmethod
    def __iter__(self) -> Iterator[Card]:
        raise NotImplementedError

  
class CardGenerator(ABC):
    """api of service supporting card generation from specification"""
    
    @abstractmethod
    def create_card(self, theme: str, instructions: str) -> Card:
        """
        params:
        theme -- the theme of the cards to generate
        instructions -- additonal instructions to follow when generting the card
        """
        raise NotImplementedError
    

class DeckService(ABC):
    """
    Implement access and modification to all the decks in the app.
    """
    
    @abstractmethod
    def decks(self) -> Iterator[Deck]:
        raise NotImplementedError
    
    @abstractmethod
    def get_deck(self, id: str) -> Deck|None:
        raise NotImplementedError
    
    @abstractmethod
    def add_deck(self, deck: Deck):
        """
        Add a deck to the app if the deck is already present.
        Only 1 instance of each deck will be stored by the app.
        """
        raise NotImplementedError
    
    @abstractmethod
    def remove_deck(self, id:str):
        raise NotImplementedError
    
    
    

