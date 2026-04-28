from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.models import SearchResponse, TasteProfileRequest, TasteProfileResponse
from backend.api.books import BooksService
from backend.api.itunes import ItunesService
from backend.api.spotify import SpotifyService
from backend.api.taste import build_taste_profile

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

spotify_service = SpotifyService()
itunes_service = ItunesService()
books_service = BooksService()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/api/spotify/artists", response_model=SearchResponse)
async def spotify_artists(q: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=20)) -> SearchResponse:
    try:
        return await spotify_service.search_artists(q, limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/itunes/podcasts", response_model=SearchResponse)
async def itunes_podcasts(q: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=20)) -> SearchResponse:
    try:
        return await itunes_service.search_podcasts(q, limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/books/audiobooks", response_model=SearchResponse)
async def audiobooks(q: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=20)) -> SearchResponse:
    try:
        return await books_service.search_audiobooks(q, limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/taste/profile", response_model=TasteProfileResponse)
def taste_profile(payload: TasteProfileRequest) -> TasteProfileResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    return build_taste_profile(payload, openai_api_key=api_key)
