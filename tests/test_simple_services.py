import unittest

from anki_scroll.services import Card
from anki_scroll.simple_services import SimpleDeck, SimpleDeckService


class TestSimpleDeck(unittest.TestCase):
    def test_name(self):
        deck = SimpleDeck("biology")
        self.assertEqual(deck.name(), "biology")

    def test_id(self):
        deck_a = SimpleDeck("science")
        deck_b = SimpleDeck("science")
        deck_c = SimpleDeck("math")
        self.assertEqual(deck_a.id(), deck_b.id())
        self.assertNotEqual(deck_a.id(), deck_c.id())

    def test_add(self):
        deck = SimpleDeck("history")
        card = Card(question="q", answer="a")
        deck.add(card)
        self.assertIn(card, list(deck))

    def test_remove(self):
        deck = SimpleDeck("literature")
        card = Card(question="q", answer="a")
        deck.add(card)
        deck.remove(card)
        self.assertNotIn(card, list(deck))

    def test_iter(self):
        deck = SimpleDeck("art")
        card_a = Card(question="a", answer="1")
        card_b = Card(question="b", answer="2")
        deck.add(card_a)
        deck.add(card_b)
        self.assertEqual(list(deck), [card_a, card_b])


class TestSimpleDeckService(unittest.TestCase):
    def test_decks(self):
        service = SimpleDeckService()
        deck = SimpleDeck("one")
        service.add_deck(deck)
        self.assertIn(deck, list(service.decks()))

    def test_get_deck(self):
        service = SimpleDeckService()
        deck = SimpleDeck("two")
        service.add_deck(deck)
        self.assertIs(service.get_deck(deck.id()), deck)

    def test_add_deck(self):
        service = SimpleDeckService()
        deck_a = SimpleDeck("shared")
        deck_b = SimpleDeck("shared")
        service.add_deck(deck_a)
        service.add_deck(deck_b)
        self.assertIs(service.get_deck(deck_a.id()), deck_a)

    def test_remove_deck(self):
        service = SimpleDeckService()
        deck = SimpleDeck("temp")
        service.add_deck(deck)
        service.remove_deck(deck.id())
        self.assertIsNone(service.get_deck(deck.id()))


if __name__ == "__main__":
    unittest.main()
