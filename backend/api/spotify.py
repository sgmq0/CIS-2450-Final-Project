from __future__ import annotations

import base64

import httpx

from backend.config import get_settings
from backend.models import MediaItem, SearchResponse

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"


class SpotifyService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def _get_access_token(self) -> str:
        client_id = self.settings.spotify_client_id
        client_secret = self.settings.spotify_client_secret
        if not client_id or not client_secret:
            raise ValueError("Spotify credentials are missing. Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to .env.")

        raw = f"{client_id}:{client_secret}".encode("utf-8")
        auth = base64.b64encode(raw).decode("utf-8")

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
            )
            response.raise_for_status()
            return response.json()["access_token"]

    async def search_artists(self, query: str, limit: int = 5) -> SearchResponse:
        token = await self._get_access_token()
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{API_BASE}/search",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": query, "type": "artist", "limit": limit},
            )
            response.raise_for_status()
            data = response.json()

        items = []
        for artist in data.get("artists", {}).get("items", []):
            items.append(
                MediaItem(
                    id=artist["id"],
                    name=artist["name"],
                    genres=artist.get("genres", []),
                    source="spotify",
                    metadata={
                        "popularity": artist.get("popularity"),
                        "followers": artist.get("followers", {}).get("total"),
                    },
                )
            )
        return SearchResponse(query=query, items=items)
