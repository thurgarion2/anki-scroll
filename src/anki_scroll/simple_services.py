"""
Simple default implementation for all the services.
They can be replaced later by more complex implementations.
"""
from __future__ import annotations

from collections.abc import Iterator
from hashlib import sha256
from typing import Dict
from uuid import uuid4

from anki_scroll.services import (
    Card,
    CardGenerator,
    CardSpec,
    CardSpecService,
    Deck,
    DeckService,
)

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
    """Deterministic placeholder generator based on the spec."""

    def __init__(self) -> None:
        self._counter = 0

    def create_card(self, theme: str, instructions: str) -> Card:
        self._counter += 1
        theme_text = theme.strip() or "General"
        instruction_text = instructions.strip() or "Review the basics"
        question = f"{theme_text} concept {self._counter}"
        answer = f"{instruction_text} — detail {self._counter}"
        return Card(question=question, answer=answer)


class SimpleCardSpecService(CardSpecService):
    """In-memory storage for card specifications."""

    def __init__(self) -> None:
        self._specs: Dict[str, CardSpec] = {}

    def save(
        self,
        deck_id: str,
        theme: str,
        instructions: str,
        spec_id: str | None = None,
    ) -> CardSpec:
        spec_key = spec_id or str(uuid4())
        spec = self._specs.get(spec_key)
        if spec is None:
            spec = CardSpec(
                id=spec_key,
                deck_id=deck_id,
                theme=theme.strip(),
                instructions=instructions.strip(),
            )
        else:
            spec.deck_id = deck_id
            spec.theme = theme.strip()
            spec.instructions = instructions.strip()
        self._specs[spec_key] = spec
        return spec

    def get(self, spec_id: str) -> CardSpec | None:
        return self._specs.get(spec_id)
    
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
