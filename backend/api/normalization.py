from __future__ import annotations


def normalize_genre(raw: str) -> str:
    genre = raw.lower().strip().replace("&", "and")
    genre = genre.replace("/", " ").replace("_", " ")
    genre = " ".join(genre.split())

    rules = [
        ("pop", "pop"),
        ("rock", "rock"),
        ("hip hop", "hip-hop"),
        ("rap", "hip-hop"),
        ("r&b", "rnb"),
        ("rhythm and blues", "rnb"),
        ("country", "country"),
        ("jazz", "jazz"),
        ("classical", "classical"),
        ("electronic", "electronic"),
        ("dance", "electronic"),
        ("indie", "indie"),
        ("news", "news"),
        ("comedy", "comedy"),
        ("business", "business"),
        ("education", "education"),
        ("history", "history"),
        ("health", "health"),
        ("fitness", "health"),
        ("science", "science"),
        ("technology", "technology"),
        ("society", "society-culture"),
        ("culture", "society-culture"),
        ("self-help", "self-help"),
        ("self help", "self-help"),
        ("psychology", "psychology"),
        ("personal growth", "self-help"),
        ("biography", "biography"),
        ("memoir", "biography"),
        ("fiction", "fiction"),
        ("fantasy", "fantasy"),
        ("romance", "romance"),
        ("mystery", "mystery"),
        ("thriller", "thriller"),
    ]

    for needle, normalized in rules:
        if needle in genre:
            return normalized
    return genre


def normalize_genres(genres: list[str]) -> list[str]:
    cleaned = [normalize_genre(g) for g in genres if g and g.strip()]
    return sorted(set(cleaned))
