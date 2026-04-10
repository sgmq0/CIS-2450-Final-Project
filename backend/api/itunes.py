from __future__ import annotations

import httpx

from backend.models import MediaItem, SearchResponse

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"


class ItunesService:
    async def search_podcasts(self, query: str, limit: int = 5) -> SearchResponse:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                ITUNES_SEARCH_URL,
                params={"term": query, "media": "podcast", "limit": limit},
            )
            response.raise_for_status()
            data = response.json()

        items = []
        for result in data.get("results", []):
            genre = result.get("primaryGenreName")
            items.append(
                MediaItem(
                    id=str(result.get("collectionId") or result.get("trackId") or result.get("artistId")),
                    name=result.get("collectionName") or result.get("trackName") or "Unknown Podcast",
                    genres=[genre] if genre else [],
                    source="itunes",
                    creator=result.get("artistName"),
                    metadata={
                        "feed_url": result.get("feedUrl"),
                        "release_date": result.get("releaseDate"),
                    },
                )
            )
        return SearchResponse(query=query, items=items)
