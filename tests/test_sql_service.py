import sqlite3
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path

from anki_scroll.services import Card
from anki_scroll.simple_services import SimpleDeck
from anki_scroll.sql_service import SqlConfig, SqlDeckService


class SqlServiceTestCase(unittest.TestCase):
    def setUp(self):
        self._tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tempdir.name) / "test.sqlite"
        self.config = SqlConfig(database=str(self.db_path))
        self.service = SqlDeckService(config=self.config)

    def tearDown(self):
        self._tempdir.cleanup()

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn


class TestSqlDeck(SqlServiceTestCase):
    def test_name(self):
        deck = self.service.create_deck("History")
        self.assertIsNotNone(deck)
        self.assertEqual(deck.name(), "History")

    def test_id(self):
        deck = self.service.create_deck("Science")
        self.assertIsNotNone(deck)
        expected = sha256("Science".encode("utf-8")).hexdigest()
        self.assertEqual(deck.id(), expected)

    def test_add(self):
        deck = self.service.create_deck("Add Deck")
        self.assertIsNotNone(deck)
        card = Card(question="Q", answer="A")
        deck.add(card)
        
        cards = list(deck)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].question, "Q")
        self.assertEqual(cards[0].answer, "A")

    def test_remove(self):
        deck = self.service.create_deck("Remove Deck")
        self.assertIsNotNone(deck)
        card = Card(question="Q", answer="A")
        deck.add(card)
        deck.remove(card)
        cards = list(deck)
        self.assertEqual(len(cards), 0)

    def test_iter(self):
        deck = self.service.create_deck("Iter Deck")
        self.assertIsNotNone(deck)
        card_a = Card(question="A?", answer="1")
        card_b = Card(question="B?", answer="2")
        deck.add(card_a)
        deck.add(card_b)
        cards = list(deck)
        self.assertEqual(cards, [card_a, card_b])


class TestSqlDeckService(SqlServiceTestCase):
    def test_decks(self):
        deck = self.service.create_deck("Deck List")
        self.assertIsNotNone(deck)
        decks = list(self.service.decks())
        self.assertTrue(any(candidate.id() == deck.id() for candidate in decks))

    def test_get_deck(self):
        deck = self.service.create_deck("Lookup Deck")
        self.assertIsNotNone(deck)
        fetched = self.service.get_deck(deck.id())
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id(), deck.id())

    def test_add_deck(self):
        donor_service = SimpleDeck("Donor")
        donor_card = Card(question="Origin", answer="Deck")
        donor_service.add(donor_card)
        self.service.add_deck(donor_service)
        retrieved = self.service.get_deck(donor_service.id())
        self.assertIsNotNone(retrieved)
        self.assertEqual(list(retrieved), [donor_card])

    def test_create_deck(self):
        deck = self.service.create_deck("Factory Deck")
        self.assertIsNotNone(deck)
        duplicate = self.service.create_deck("Factory Deck")
        self.assertIsNone(duplicate)

    def test_remove_deck(self):
        deck = self.service.create_deck("Disposable")
        self.assertIsNotNone(deck)
        self.service.remove_deck(deck.id())
        self.assertIsNone(self.service.get_deck(deck.id()))


if __name__ == "__main__":
    unittest.main()
