from pydantic import BaseModel, Field


class MediaItem(BaseModel):
    id: str
    name: str
    genres: list[str] = Field(default_factory=list)
    source: str
    creator: str | None = None
    metadata: dict = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    items: list[MediaItem]


class TasteProfileRequest(BaseModel):
    music_items: list[MediaItem] = Field(default_factory=list)
    podcast_items: list[MediaItem] = Field(default_factory=list)
    audiobook_items: list[MediaItem] = Field(default_factory=list)


class PairwiseOverlap(BaseModel):
    music_podcast: float
    music_audiobook: float
    podcast_audiobook: float


class TasteProfileResponse(BaseModel):
    normalized_music_genres: list[str]
    normalized_podcast_genres: list[str]
    normalized_audiobook_genres: list[str]
    top_genres: list[str]
    consistency_score: int
    diversity_score: int
    balance_score: int
    overall_score: int
    pairwise_overlap: PairwiseOverlap
    interpretation: str


class TasteItem(BaseModel):
    id: str
    name: str
    source: str          # "spotify" | "itunes" | "google_books"
    genres: list[str]


class TasteModelRequest(BaseModel):
    music_items: list[TasteItem] = []
    podcast_items: list[TasteItem] = []
    audiobook_items: list[TasteItem] = []

