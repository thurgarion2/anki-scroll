from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Callable, Iterator, Self
from dotenv import load_dotenv

from anki_scroll.services import Card, Deck, DeckService


@dataclass(slots=True)
class SqlConfig:
    """
    Contain all the parameter to connect to the sql database.
    """

    database: str

    @classmethod
    def load(cls) -> Self:
        """
        Load configuration from the environment.
        ANKI_SCROLL_DB_PATH can point to a sqlite file path or sqlite URI.
        Defaults to ``anki_scroll.sqlite3`` in the current working directory.
        """
        load_dotenv()
        db_path = os.environ.get("ANKI_SCROLL_DB_PATH")
        if not db_path:
            db_path = str(Path.cwd() / "anki_scroll.sqlite3")
        return cls(database=db_path)


class SqlDeck(Deck):
    """
    A deck that uses sql lite as backend.
    When trying to perform an operation, if the deck cannot be found in hte db; raise an error.
    """

    def __init__(
        self,
        deck_id: str,
        name: str,
        connection_factory: Callable[[], sqlite3.Connection],
    ) -> None:
        self._id = deck_id
        self._name = name
        self._connection_factory = connection_factory

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = self._connection_factory()
        try:
            yield conn
        finally:
            conn.close()

    def _assert_exists(self, conn: sqlite3.Connection) -> None:
        cursor = conn.execute("SELECT 1 FROM decks WHERE id = ?", (self._id,))
        if cursor.fetchone() is None:
            raise LookupError(f"Deck '{self._id}' does not exist in the database.")

    def name(self) -> str:
        return self._name

    def id(self) -> str:
        return self._id

    def add(self, card: Card):
        with self._connect() as conn:
            self._assert_exists(conn)
            conn.execute(
                "INSERT INTO cards (deck_id, question, answer) VALUES (?, ?, ?)",
                (self._id, card.question, card.answer),
            )
            conn.commit()

    def remove(self, card: Card):
        with self._connect() as conn:
            self._assert_exists(conn)
            conn.execute(
                """
                DELETE FROM cards
                WHERE rowid IN (
                    SELECT rowid FROM cards
                    WHERE deck_id = ? AND question = ? AND answer = ?
                    LIMIT 1
                )
                """,
                (self._id, card.question, card.answer),
            )
            conn.commit()

    def __iter__(self) -> Iterator[Card]:
        with self._connect() as conn:
            self._assert_exists(conn)
            rows = conn.execute(
                "SELECT question, answer FROM cards WHERE deck_id = ? ORDER BY rowid",
                (self._id,),
            ).fetchall()
        for row in rows:
            yield Card(question=row["question"], answer=row["answer"])


class SqlDeckService(DeckService):
    """
    A deck service that use a sql lite backend.
    The tables supporting the service should always exists in the db.
    """

    def __init__(self, config: SqlConfig | None = None) -> None:
        self._config = config or SqlConfig.load()
        self._database = self._config.database
        self._ensure_directory()
        self._initialize_schema()

    def _ensure_directory(self) -> None:
        if self._database in (":memory:",):
            return
        if self._database.startswith("file:"):
            return
        db_path = Path(self._database)
        if not db_path.name:
            return
        db_path.parent.mkdir(parents=True, exist_ok=True)

    def _new_connection(self) -> sqlite3.Connection:
        use_uri = self._database.startswith("file:")
        conn = sqlite3.connect(self._database, uri=use_uri)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = self._new_connection()
        try:
            yield conn
        finally:
            conn.close()

    def _initialize_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS decks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE
                );
                CREATE TABLE IF NOT EXISTS cards (
                    deck_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    FOREIGN KEY(deck_id) REFERENCES decks(id) ON DELETE CASCADE
                );
                """
            )
            conn.commit()

    def _deck_exists(self, conn: sqlite3.Connection, deck_id: str) -> bool:
        cursor = conn.execute("SELECT 1 FROM decks WHERE id = ?", (deck_id,))
        return cursor.fetchone() is not None

    def _row_to_deck(self, deck_row: sqlite3.Row) -> SqlDeck:
        return SqlDeck(
            deck_id=deck_row["id"],
            name=deck_row["name"],
            connection_factory=self._new_connection,
        )

    def decks(self) -> Iterator[Deck]:
        with self._connect() as conn:
            rows = conn.execute("SELECT id, name FROM decks ORDER BY name").fetchall()
        for row in rows:
            yield self._row_to_deck(row)

    def get_deck(self, id: str) -> Deck | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name FROM decks WHERE id = ?", (id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_deck(row)

    def add_deck(self, deck: Deck):
        with self._connect() as conn:
            if self._deck_exists(conn, deck.id()):
                return
            conn.execute(
                "INSERT INTO decks (id, name) VALUES (?, ?)",
                (deck.id(), deck.name()),
            )
            cards = list(deck)
            if cards:
                conn.executemany(
                    "INSERT INTO cards (deck_id, question, answer) VALUES (?, ?, ?)",
                    [
                        (deck.id(), card.question, card.answer)
                        for card in cards
                    ],
                )
            conn.commit()

    def create_deck(self, name: str) -> Deck | None:
        """Create a deck unless it already exists."""
        deck_name = name.strip()
        digest = sha256(deck_name.encode("utf-8")).hexdigest()
        with self._connect() as conn:
            if self._deck_exists(conn, digest):
                return None
            conn.execute(
                "INSERT INTO decks (id, name) VALUES (?, ?)",
                (digest, deck_name),
            )
            conn.commit()
        return SqlDeck(digest, deck_name, self._new_connection)

    def remove_deck(self, id: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM decks WHERE id = ?", (id,))
            conn.commit()
