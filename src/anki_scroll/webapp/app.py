"""FastAPI web application for Anki Scroll mock UI."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from anki_scroll.services import (
    Card,
    CardGenerator,
    CardSpec,
    CardSpecService,
    Deck,
    DeckService,
)
from anki_scroll.simple_services import (
    SimpleCardGenerator,
    SimpleCardSpecService,
    SimpleDeck,
    SimpleDeckService,
)


TEMPLATES_DIR = Path(__file__).with_name("templates")
STATIC_DIR = Path(__file__).with_name("static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

DEFAULT_DECK_NAME = "Explorer Deck"


class WebState:
    """Hold in-memory data for the demo web app."""

    def __init__(
        self,
        deck_service: Optional[DeckService] = None,
        card_spec_service: Optional[CardSpecService] = None,
        card_generator: Optional[CardGenerator] = None,
    ) -> None:
        self.deck_service = deck_service or SimpleDeckService()
        self.card_spec_service = card_spec_service or SimpleCardSpecService()
        self.card_generator = card_generator or SimpleCardGenerator()
        self._bootstrap()

    def _bootstrap(self) -> None:
        deck = SimpleDeck(DEFAULT_DECK_NAME)
        deck.add(Card(question="What is spaced repetition?", answer="A study technique."))
        deck.add(
            Card(
                question="Why use flashcards?",
                answer="They reinforce active recall.",
            )
        )
        self.deck_service.add_deck(deck)

    def save_spec(
        self, deck_id: str, theme: str, instructions: str, spec_id: Optional[str] = None
    ) -> CardSpec:
        spec = self.card_spec_service.save(deck_id, theme, instructions, spec_id)
        return spec

    def get_spec(self, spec_id: str) -> CardSpec|None:
        spec = self.card_spec_service.get(spec_id)
        return spec


def build_app(state: Optional[WebState] = None) -> FastAPI:
    app = FastAPI(title="Anki Scroll Web")
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.state.web_state = state or WebState()

    def _get_state(request: Request) -> WebState:
        return request.app.state.web_state

    def _get_deck_or_404(state: WebState, deck_id: str) -> Deck:
        deck = state.deck_service.get_deck(deck_id)
        if deck is None:
            raise HTTPException(status_code=404, detail="Deck not found")
        return deck
    
    @app.get("/")
    async def index(request: Request) -> RedirectResponse:
        return RedirectResponse(url=f"/home/", status_code=303)

    @app.get("/home/", response_class=HTMLResponse)
    async def home(request: Request) -> HTMLResponse:
        state = _get_state(request)
        decks = []
        for deck in state.deck_service.decks():
            cards = list(deck)
            decks.append(
                {
                    "id": deck.id(),
                    "name": deck.name(),
                    "count": len(cards),
                }
            )
        return templates.TemplateResponse(
            request,
            "home.html",
            {"decks": decks},
        )

    @app.post("/home/new-deck")
    async def create_deck(request: Request, name: str = Form(...)) -> RedirectResponse:
        state = _get_state(request)
        deck_name = name.strip()
        candidate = SimpleDeck(deck_name)
        existing = state.deck_service.get_deck(candidate.id())
        if existing is None:
            state.deck_service.add_deck(candidate)
            target = candidate
        else:
            target = existing
        return RedirectResponse(url=f"/deck/{target.id()}", status_code=303)

    @app.get("/deck/{deck_id}", response_class=HTMLResponse)
    async def deck_view(request: Request, deck_id: str) -> HTMLResponse:
        state = _get_state(request)
        deck = _get_deck_or_404(state, deck_id)
        cards = list(deck)
        return templates.TemplateResponse(
            request,
            "deck.html",
            {
                "deck_id": deck_id,
                "deck_name": deck.name(),
                "cards": cards,
            },
        )

    @app.post("/deck/{deck_id}/cards/delete")
    async def delete_card(
        request: Request,
        deck_id: str,
        question: str = Form(...),
        answer: str = Form(...),
    ) -> RedirectResponse:
        state = _get_state(request)
        deck = _get_deck_or_404(state, deck_id)
        try:
            deck.remove(Card(question=question, answer=answer))
        except ValueError:
            pass
        return RedirectResponse(url=f"/deck/{deck_id}", status_code=303)

    @app.get("/create_card/{deck_id}/", response_class=HTMLResponse)
    async def create_spec(
        request: Request,
        deck_id: str,
        spec_id: Optional[str] = None,
    ) -> HTMLResponse:
        state = _get_state(request)
        _get_deck_or_404(state, deck_id)
        spec = None
        if spec_id:
            spec = state.get_spec(spec_id)
        return templates.TemplateResponse(
            request,
            "create_spec.html",
            {
                "deck_id": deck_id,
                "spec": spec,
            },
        )

    @app.post("/create_card/{deck_id}/")
    async def save_spec(
        request: Request,
        deck_id: str,
        theme: str = Form(""),
        instructions: str = Form(""),
        spec_id: Optional[str] = Form(None),
    ) -> RedirectResponse:
        state = _get_state(request)
        _get_deck_or_404(state, deck_id)
        spec = state.save_spec(deck_id, theme, instructions, spec_id)
        return RedirectResponse(
            url=f"/select/{deck_id}/{spec.id}", status_code=303
        )

    @app.get("/select/{deck_id}/{spec_id}", response_class=HTMLResponse)
    async def select_cards(request: Request, deck_id: str, spec_id: str) -> HTMLResponse:
        state = _get_state(request)
        _get_deck_or_404(state, deck_id)
        spec = state.get_spec(spec_id)
        if spec is None:
            raise HTTPException(status_code=404, detail="Spec not found")
        card = state.card_generator.create_card(spec.theme, spec.instructions)

        return templates.TemplateResponse(
            request,
            "select.html",
            {
                "deck_id": deck_id,
                "spec": spec,
                "card": card,
            },
        )

    @app.post("/select/{deck_id}/{spec_id}")
    async def select_card(
        request: Request,
        deck_id: str,
        spec_id: str,
        question: str = Form(...),
        answer: str = Form(...),
    ) -> RedirectResponse:
        state = _get_state(request)
        deck = _get_deck_or_404(state, deck_id)
        spec = state.get_spec(spec_id)
        if spec is None:
            raise HTTPException(status_code=404, detail="Spec not found")
        deck.add(Card(question=question, answer=answer))
        return RedirectResponse(
            url=f"/select/{deck_id}/{spec_id}",
            status_code=303,
        )

    return app


app = build_app()

__all__ = ["build_app", "WebState", "DEFAULT_DECK_NAME"]
