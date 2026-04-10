from __future__ import annotations

from collections import Counter

from backend.models import PairwiseOverlap, TasteProfileRequest, TasteProfileResponse
from backend.api.normalization import normalize_genres


def _collect_genres(items) -> list[str]:
    genres: list[str] = []
    for item in items:
        genres.extend(item.genres)
    return genres


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _diversity_score(all_genres: list[str]) -> int:
    unique_count = len(set(all_genres))
    return round(min(unique_count / 12, 1.0) * 100)


def _balance_score(*genre_lists: list[str]) -> int:
    sizes = [len(set(g)) for g in genre_lists]
    if max(sizes, default=0) == 0:
        return 0
    return round((min(sizes) / max(sizes)) * 100)


def _interpret(overall: int, consistency: int, diversity: int) -> str:
    if overall >= 80 and consistency >= 70:
        return "This user has a strong, coherent media identity with clear overlap across music, podcasts, and audiobooks."
    if diversity >= 75 and consistency < 45:
        return "This user has broad and exploratory taste, with meaningful variety across media formats rather than one dominant theme."
    if overall >= 60:
        return "This user shows moderate alignment across media, mixing a few recurring interests with some variety."
    return "This user’s media taste is still diffuse or lightly sampled, so the profile suggests experimentation more than a single clear pattern."


def build_taste_profile(payload: TasteProfileRequest) -> TasteProfileResponse:
    music_genres = normalize_genres(_collect_genres(payload.music_items))
    podcast_genres = normalize_genres(_collect_genres(payload.podcast_items))
    audiobook_genres = normalize_genres(_collect_genres(payload.audiobook_items))

    music_set = set(music_genres)
    podcast_set = set(podcast_genres)
    audiobook_set = set(audiobook_genres)

    music_podcast = _jaccard(music_set, podcast_set)
    music_audiobook = _jaccard(music_set, audiobook_set)
    podcast_audiobook = _jaccard(podcast_set, audiobook_set)

    consistency_score = round(((music_podcast + music_audiobook + podcast_audiobook) / 3) * 100)
    all_genres = music_genres + podcast_genres + audiobook_genres
    diversity_score = _diversity_score(all_genres)
    balance_score = _balance_score(music_genres, podcast_genres, audiobook_genres)
    overall_score = round(0.5 * consistency_score + 0.3 * diversity_score + 0.2 * balance_score)

    counts = Counter(all_genres)
    top_genres = [genre for genre, _ in counts.most_common(8)]

    return TasteProfileResponse(
        normalized_music_genres=music_genres,
        normalized_podcast_genres=podcast_genres,
        normalized_audiobook_genres=audiobook_genres,
        top_genres=top_genres,
        consistency_score=consistency_score,
        diversity_score=diversity_score,
        balance_score=balance_score,
        overall_score=overall_score,
        pairwise_overlap=PairwiseOverlap(
            music_podcast=round(music_podcast, 3),
            music_audiobook=round(music_audiobook, 3),
            podcast_audiobook=round(podcast_audiobook, 3),
        ),
        interpretation=_interpret(overall_score, consistency_score, diversity_score),
    )
