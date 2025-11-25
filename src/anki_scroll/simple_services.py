"""
Simple default implementation for all the services.
They can be replaced later by more complex implementations.
"""
from __future__ import annotations

from collections.abc import Iterator
from hashlib import sha256
from typing import Dict

from anki_scroll.services import Card, CardGenerator, Deck, DeckService

class SimpleDeck(Deck):
    """simple in-memory deck implementation"""

    def __init__(self, name: str) -> None:
        self._name = name
        self._cards: list[Card] = []

    def name(self) -> str:
        return self._name

    def id(self) -> str:
        digest = sha256(self._name.encode("utf-8"))
        return digest.hexdigest()

    def add(self, card: Card):
        self._cards.append(card)

    def remove(self, card: Card):
        try:
            self._cards.remove(card)
        except ValueError:
            pass

    def __iter__(self) -> Iterator[Card]:
        return iter(self._cards)


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

    def __init__(self) -> None:
        self._decks: Dict[str, Deck] = {}

    def decks(self) -> Iterator[Deck]:
        return iter(self._decks.values())

    def get_deck(self, id: str) -> Deck | None:
        return self._decks.get(id)

    def add_deck(self, deck: Deck):
        if deck.id() not in self._decks:
            self._decks[deck.id()] = deck

    def remove_deck(self, id: str):
        self._decks.pop(id, None)
