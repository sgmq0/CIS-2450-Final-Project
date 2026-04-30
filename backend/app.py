from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.models import MediaItem, SearchResponse, TasteProfileRequest, TasteProfileResponse, TasteModelRequest, AnalysisRequest
from backend.api.books import BooksService
from backend.api.itunes import ItunesService
from backend.api.spotify import SpotifyService
from backend.api.taste import build_taste_profile
from backend.api.modeling import run_feature_engineering, run_ensemble, run_feature_importance

from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

import requests

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


def get_genres_from_musicbrainz(artist_name: str, limit: int) -> list[MediaItem]:
    search_res = requests.get(
        "https://musicbrainz.org/ws/2/artist/",
        params={"query": artist_name, "fmt": "json", "limit": limit, "inc": "tags"},
        headers={"User-Agent": "MediaTasteApp/1.0 (feng.r018@gmail.com)"}
    ).json()

    if not search_res.get("artists"):
        return []

    items = []
    for artist in search_res["artists"][:limit]:
        tags = sorted(artist.get("tags", []), key=lambda t: -t["count"])
        items.append(MediaItem(
            id=artist["id"],
            name=artist["name"],
            source="musicbrainz",
            genres=[t["name"] for t in tags[:8]],
            creator=None,
            metadata={"score": artist.get("score", 0)}
        ))

    return items


@app.get("/api/spotify/artists", response_model=SearchResponse)
async def spotify_artists(q: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=20)) -> SearchResponse:
    try:

        results = get_genres_from_musicbrainz(q, limit)

        return SearchResponse(
            query=q,
            items=[
                MediaItem(**item) if isinstance(item, dict) else item
                for item in results
            ]
        )
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


@app.post("/api/taste/model")
def model_taste(body: TasteModelRequest):
    all_items = body.music_items + body.podcast_items + body.audiobook_items

    if len(all_items) < 2:
        return {"error": "Add at least 2 items to model your taste."}

    # binary genre matrix, like notebook's MultiLabelBinarizer (feature engineering)
    mlb = MultiLabelBinarizer()
    genre_matrix = mlb.fit_transform([item.genres for item in all_items])
    genre_classes = mlb.classes_

    # cosine similarity instead of k means because we're running it on way less data points
    sim_matrix = cosine_similarity(genre_matrix)

    # each item's fit score = avg similarity to all other items
    fit_scores = sim_matrix.mean(axis=1).tolist()

    # outliers = lowest fit score
    sorted_by_fit = sorted(
        zip([i.name for i in all_items], [i.source for i in all_items], fit_scores),
        key=lambda x: x[2]
    )
    outliers = [{"name": n, "source": s, "score": round(sc, 3)}
                for n, s, sc in sorted_by_fit[:2]]

    # top genres across full profile
    genre_freq = genre_matrix.sum(axis=0)
    top_genre_indices = np.argsort(genre_freq)[::-1][:8]
    top_genres = [genre_classes[i] for i in top_genre_indices]

    # bridge genres-- appear in all 3 sources
    def genres_for(items): 
        return set(g for item in items for g in item.genres)

    music_genres = genres_for(body.music_items)
    podcast_genres = genres_for(body.podcast_items)
    audiobook_genres = genres_for(body.audiobook_items)
    bridge_genres = list(music_genres & podcast_genres & audiobook_genres)

    # genre diversity -> fraction of genres that appear at least once
    genre_diversity = round(
        float(np.count_nonzero(genre_freq)) / max(len(genre_classes), 1), 3
    )

    return {
        "fit_scores": [
            {"name": all_items[i].name, "source": all_items[i].source, "score": round(fit_scores[i], 3)}
            for i in range(len(all_items))
        ],
        "outliers": outliers,
        "top_genres": top_genres,
        "bridge_genres": bridge_genres,
        "genre_diversity": genre_diversity,
    }


@app.post("/api/taste/feature-engineering")
def feature_engineering(body: AnalysisRequest):
    return run_feature_engineering(body.all_items())


@app.post("/api/taste/ensemble")
def ensemble(body: AnalysisRequest):
    return run_ensemble(body.all_items())


@app.post("/api/taste/feature-importance")
def feature_importance(body: AnalysisRequest):
    return run_feature_importance(body.all_items())
