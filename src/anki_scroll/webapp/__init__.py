"""Expose the FastAPI application builder for the web UI."""

from .app import DEFAULT_DECK_NAME, WebState, build_app

__all__ = ["build_app", "WebState", "DEFAULT_DECK_NAME"]
