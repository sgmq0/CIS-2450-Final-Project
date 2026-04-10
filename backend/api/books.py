from __future__ import annotations

import httpx

from backend.config import get_settings
from backend.models import MediaItem, SearchResponse

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"


class BooksService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def search_audiobooks(self, query: str, limit: int = 5) -> SearchResponse:
        params = {"q": query, "maxResults": limit, "printType": "books"}
        if self.settings.google_books_api_key:
            params["key"] = self.settings.google_books_api_key

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(GOOGLE_BOOKS_URL, params=params)
            response.raise_for_status()
            data = response.json()

        items = []
        for result in data.get("items", []):
            info = result.get("volumeInfo", {})
            items.append(
                MediaItem(
                    id=result.get("id", "unknown-book-id"),
                    name=info.get("title", "Unknown Title"),
                    genres=info.get("categories", []),
                    source="google_books",
                    creator=", ".join(info.get("authors", [])) if info.get("authors") else None,
                    metadata={
                        "published_date": info.get("publishedDate"),
                        "page_count": info.get("pageCount"),
                        "language": info.get("language"),
                    },
                )
            )
        return SearchResponse(query=query, items=items)
