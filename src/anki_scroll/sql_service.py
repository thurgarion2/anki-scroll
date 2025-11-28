from anki_scroll.services import Deck, Card, DeckService
from typing import Iterator, Self


class SqlConfig:
    """
    Contain all the parameter to connect to the sql database.
    """
    
    @classmethod
    def load(cls) -> Self:
        pass
        

class SqlDeck(Deck):
    """
    A deck that uses sql lite as backend.
    When trying to perform an operation, if the deck cannot be found in hte db; raise an error.
    """
    
    # codex the deck will store in memory name and id as they are immutable for the rest you should
    # always do an sql query
    
    def name(self) -> str:
        pass
    
    def id(self) -> str:
        pass

    def add(self, card: Card):
        pass

    def remove(self, card: Card):
        pass

    def __iter__(self) -> Iterator[Card]:
        pass
    

class SqlDeckService(DeckService):
    """
    A deck service that use a sql lite backend.
    The tables supporting the service should always exists in the db.
    """
    
    def decks(self) -> Iterator[Deck]:
        raise NotImplementedError
    
    def get_deck(self, id: str) -> Deck|None:
        raise NotImplementedError
    
    def add_deck(self, deck: Deck):
        raise NotImplementedError
    
    def create_deck(self, name: str) -> Deck | None:
        """Create a deck unless it already exists."""
        raise NotImplementedError
    
    def remove_deck(self, id:str):
        raise NotImplementedError
