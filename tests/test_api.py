import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from anki_scroll.api import Card, SimpleDeck, SimpleCardGenerator


class TestSimpleDeck(unittest.TestCase):
    def setUp(self):
        self.deck = SimpleDeck()
        self.card = Card(question="What is AI?", answer="Artificial intelligence")

    def test_add(self):
        self.deck.add(self.card)
        self.assertIn(self.card, list(self.deck))

    def test_remove(self):
        self.deck.add(self.card)
        self.deck.remove(self.card)
        self.assertNotIn(self.card, list(self.deck))

    def test_iterator(self):
        extra = Card(question="What is ML?", answer="Machine learning")
        self.deck.add(self.card)
        self.deck.add(extra)
        cards_in_deck = list(self.deck)
        self.assertCountEqual(cards_in_deck, [self.card, extra])

    def test_add_same_instance_only_once(self):
        self.deck.add(self.card)
        self.deck.add(self.card)
        self.assertEqual(list(self.deck).count(self.card), 1)

    def test_add_equal_but_distinct_instances(self):
        duplicate = Card(question="What is AI?", answer="Artificial intelligence")
        self.deck.add(self.card)
        self.deck.add(duplicate)
        cards_in_deck = list(self.deck)
        self.assertEqual(len(cards_in_deck), 2)
        self.assertEqual({id(self.card), id(duplicate)}, {id(card) for card in cards_in_deck})


class TestSimpleCardGenerator(unittest.TestCase):
    def test_create_card_returns_copy(self):
        template = Card(question="Theme?", answer="Instructions.")
        generator = SimpleCardGenerator(template)
        generated = generator.create_card("anything", "ignored")
        self.assertIsNot(template, generated)
        self.assertEqual(template, generated)


if __name__ == "__main__":
    unittest.main()
