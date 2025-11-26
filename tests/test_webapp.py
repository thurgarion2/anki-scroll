import unittest

import httpx

from anki_scroll.simple_services import SimpleDeck
from anki_scroll.webapp import DEFAULT_DECK_NAME, WebState, build_app


class WebAppTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        state = WebState()
        self.app = build_app(state)
        transport = httpx.ASGITransport(app=self.app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://test")
        self.default_deck_id = SimpleDeck(DEFAULT_DECK_NAME).id()

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_home_endpoint(self):
        response = await self.client.get("/home/")
        self.assertEqual(response.status_code, 200)

    async def test_create_deck_endpoint(self):
        response = await self.client.post(
            "/home/new-deck", data={"name": "Chemistry"}, follow_redirects=False
        )
        self.assertEqual(response.status_code, 303)

    async def test_deck_view_endpoint(self):
        response = await self.client.get(f"/deck/{self.default_deck_id}")
        self.assertEqual(response.status_code, 200)

    async def test_delete_card_endpoint(self):
        deck = self.app.state.web_state.deck_service.get_deck(self.default_deck_id)
        card = list(deck)[0]
        response = await self.client.post(
            f"/deck/{self.default_deck_id}/cards/delete",
            data={"question": card.question, "answer": card.answer},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)

    async def test_create_spec_page(self):
        response = await self.client.get(f"/create_card/{self.default_deck_id}/")
        self.assertEqual(response.status_code, 200)

    async def test_save_spec_endpoint(self):
        spec_id = await self._create_spec()
        self.assertTrue(spec_id)

    async def test_select_page(self):
        spec_id = await self._create_spec()
        response = await self.client.get(f"/select/{self.default_deck_id}/{spec_id}")
        self.assertEqual(response.status_code, 200)

    async def test_select_next_endpoint(self):
        spec_id = await self._create_spec()
        # Initial load
        response = await self.client.get(f"/select/{self.default_deck_id}/{spec_id}")
        self.assertEqual(response.status_code, 200)
        # Simulate clicking "Next" which just reloads the page
        response = await self.client.get(f"/select/{self.default_deck_id}/{spec_id}")
        self.assertEqual(response.status_code, 200)

    async def test_select_choose_endpoint(self):
        spec_id = await self._create_spec()
        response = await self.client.post(
            f"/select/{self.default_deck_id}/{spec_id}",
            data={"question": "Sample question", "answer": "Sample answer"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)

    async def _create_spec(self):
        response = await self.client.post(
            f"/create_card/{self.default_deck_id}/",
            data={"theme": "Astronomy", "instructions": "Focus on basics"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        location = response.headers.get("location", "")
        return location.rsplit("/", 1)[-1] if location else None


if __name__ == "__main__":
    unittest.main()
