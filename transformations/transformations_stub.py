"""Student stub for Homework 2 transformations."""

from __future__ import annotations
import polars as pl
from typing import List, Tuple, Set, Dict
import re

from reference.transformations_hw1 import (
    transform_data,
    get_user_friendships,
    get_user_friend_counts,
    get_user_favorite_songs,
    get_songs_by_genre_and_artist,
    get_friend_recommendations,
    get_top_artists_by_friends,
    get_genre_overlap_between_users,
    get_popular_songs_among_friends,
    get_top_genres_among_friends,
    get_top_songs_per_genre,
)


def normalize_artist_name(name: str) -> str:
    # convert to lower
    name_result = name.lower()

    # remove featuring indicators and everything after them
    name_result = name_result.split("feat.")[0].split("ft.")[0].split("featuring")[0].split("with")[0]

    # remove all punctuation
    translator = str.maketrans('', '', string.punctuation)
    name_result = name_result.translate(translator)

    # normalize whitespace
    name_result = re.sub(pattern="\\s+", repl=" ", string=name_result)
    name_result = name_result.strip()

    return name_result


def levenshtein_distance(s1: str, s2: str) -> int:
    if (s1 == "" or s2 == ""):
        return max(len(s1), len(s2))

    dp = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]

    for i in range(len(dp)):
        dp[i][0] = i
    for j in range(len(dp[0])):
        dp[0][j] = j

    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + 1)

    return dp[s1.__len__()-1][s2.__len__()-1]


def qgram_similarity(s1: str, s2: str, q: int = 2) -> float:
    if (s1.__len__() == 0 or s2.__len__() == 0):
        if (s1.__len__() == s2.__len__()):
            return 1
        else: 
            return 0

    # extract all q-grams
    s1_grams = [s1[i:i+q] for i in range(len(s1)-q+1)]
    s2_grams = [s2[i:i+q] for i in range(len(s2)-q+1)]

    s1_c = collections.Counter(s1_grams)
    s2_c = collections.Counter(s2_grams)
    
    intersection = s1_c & s2_c
    union = s1_c | s2_c
    
    print(union.__len__())
 
    sim = intersection.__len__() / union.__len__()
    return sim


def embedding_distance(s1: str, s2: str, openai_api_key: str, model_name: str = "text-embedding-3-small") -> float:
    import openai
    import numpy

    openai.api_key = openai_api_key

    s1_embeddings = openai.embeddings.create(input = s1, model=model_name).data[0].embedding
    s2_embeddings = openai.embeddings.create(input = s2, model=model_name).data[0].embedding
    
    cosine_similarity = numpy.dot(s1_embeddings, s2_embeddings)
    return 1.0 - cosine_similarity


def find_matching_artists_edit_distance(
    itunes_artists: List[str],
    spotify_df: pl.DataFrame,
    threshold: int = 3
) -> pl.DataFrame:
    
    # get unique spotify artists
    unique_artists = spotify_df.explode("artists").get_column("artists").unique()

    # for each itunes artist, find the best spotify match
    # also construct the lists
    i_artist_list = []
    s_artist_list = []
    distance_list = []
    matched_list = []

    for i_artist in itunes_artists:
        max_threshold = 1e10
        best_match = ""

        for s_artist in unique_artists:
            dist = levenshtein_distance(normalize_artist_name(i_artist), normalize_artist_name(s_artist))

            if (dist <= max_threshold):
                max_threshold = dist
                best_match = s_artist

        i_artist_list.append(i_artist)
        s_artist_list.append(best_match)
        distance_list.append(max_threshold)
        if (max_threshold <= threshold):
            matched_list.append(True)
        else:
            matched_list.append(False)

    return pl.DataFrame({
        'itunes_artist': i_artist_list,
        'spotify_artist': s_artist_list,
        'distance': distance_list,
        'matched': matched_list
    })


def find_matching_artists_qgram(
    itunes_artists: List[str],
    spotify_df: pl.DataFrame,
    threshold: float = 0.6,
    q: int = 2
) -> pl.DataFrame:
    unique_artists = spotify_df.explode("artists").get_column("artists").unique()

    # for each itunes artist, find the best spotify match
    # also construct the lists
    i_artist_list = []
    s_artist_list = []
    similarity_list = []
    matched_list = []

    for i_artist in itunes_artists:
        min_threshold = 0
        best_match = ""

        for s_artist in unique_artists:
            dist = qgram_similarity(normalize_artist_name(i_artist), normalize_artist_name(s_artist), q)

            if (dist >= min_threshold):
                min_threshold = dist
                best_match = s_artist

        i_artist_list.append(i_artist)
        s_artist_list.append(best_match)
        similarity_list.append(min_threshold)
        if (min_threshold >= threshold):
            matched_list.append(True)
        else:
            matched_list.append(False)
    
    return pl.DataFrame({
        'itunes_artist': i_artist_list,
        'spotify_artist': s_artist_list,
        'similarity': similarity_list,
        'matched': matched_list
    })


def find_matching_artists_embedding(
    itunes_artists: List[str],
    spotify_df: pl.DataFrame,
    openai_api_key: str,
    threshold: float = 0.3
) -> pl.DataFrame:

    # get unique spotify artists
    unique_artists = spotify_df.explode("artists").get_column("artists").unique()

    # for each itunes artist, find the best spotify match
    # also construct the lists
    i_artist_list = []
    s_artist_list = []
    distance_list = []
    matched_list = []

    for i_artist in itunes_artists:
        max_threshold = 1e10
        best_match = ""

        for s_artist in unique_artists:
            dist = embedding_distance(normalize_artist_name(i_artist), normalize_artist_name(s_artist), openai_api_key)

            if (dist <= max_threshold):
                max_threshold = dist
                best_match = s_artist

        i_artist_list.append(i_artist)
        s_artist_list.append(best_match)
        distance_list.append(max_threshold)
        if (max_threshold <= threshold):
            matched_list.append(True)
        else:
            matched_list.append(False)

    return pl.DataFrame({
        'itunes_artist': i_artist_list,
        'spotify_artist': s_artist_list,
        'distance': distance_list,
        'matched': matched_list
    })


def compare_itunes_spotify_artists(
    itunes_artists: List[str],
    spotify_df: pl.DataFrame,
    openai_api_key: str
) -> pl.DataFrame:

    edit_distance = find_matching_artists_edit_distance(itunes_artists, spotify_df)
    qgram = find_matching_artists_qgram(itunes_artists, spotify_df)
    embedding = find_matching_artists_embedding(itunes_artists, spotify_df, openai_api_key)

    joined = edit_distance.join(
        qgram,
        on="itunes_artist",
        how='inner'
    ).rename({
        "spotify_artist": "edit_match",
        "distance": "edit_distance",
        "matched": "edit_matched",
        "spotify_artist_right": "qgram_match",
        "similarity": "qgram_similarity",
        "matched_right": "qgram_matched"
    })

    joined = joined.join(
        embedding,
        on="itunes_artist",
        how="inner"
    ).rename({
        "spotify_artist": "embedding_match",
        "distance": "embedding_distance",
        "matched": "embedding_matched",
    })

    return joined


def evaluate_matching_strategy(
    ground_truth_df: pl.DataFrame,
    matched_df: pl.DataFrame,
    strategy: str = 'edit'
) -> Dict[str, float]:

    predicted_matches = matched_df.filter((pl.col('matched') == True))

    ground_truth_df = ground_truth_df.with_columns([
        pl.col('itunes_artist').cast(pl.String),
        pl.col('spotify_artist').cast(pl.String)
    ])

    TP = ground_truth_df.join(
        predicted_matches,
        on=["itunes_artist", "spotify_artist"],
        how="inner"
    ).height

    FP = predicted_matches.join(
        ground_truth_df,
        on=["itunes_artist", "spotify_artist"],
        how="anti"
    ).height

    FN = ground_truth_df.join(
        predicted_matches,
        on=["itunes_artist", "spotify_artist"],
        how="anti"
    ).height

    if (TP + FP) == 0:
        precision = 0.0
    else:
        precision = TP / (TP + FP)

    if (TP + FN) == 0:
        recall = 0.0
    else:
        recall = TP / (TP + FN)

    if (precision + recall) == 0:
        F1 = 0.0
    else:    
        F1 = 2 * precision * recall / (precision + recall)

    return {"precision": precision, "recall": recall, "f1": F1}


def get_billboard_songs_in_spotify(billboard_df: pl.DataFrame, spotify_df: pl.DataFrame) -> pl.DataFrame:

    norm_billboard = billboard_df.select(
        pl.col("rank"),
        pl.col("title").map_elements(normalize_artist_name, return_dtype=pl.String),
        pl.col("artist").map_elements(normalize_artist_name, return_dtype=pl.String),
        pl.col("last_week_rank"), pl.col("peak_rank"), pl.col("weeks_on_chart")
    )

    new_spotify_df = spotify_df.explode("artists").select(
        pl.col("track_id"),
        pl.col("track_name").map_elements(normalize_artist_name, return_dtype=pl.String),
        pl.col("artists").map_elements(normalize_artist_name, return_dtype=pl.String),
        pl.col("album_name"), pl.col("popularity"),
        pl.col("track_genre")
    )

    combined = norm_billboard.join(
        new_spotify_df,
        left_on=[pl.col("title"), pl.col("artist")],
        right_on=[pl.col("track_name"), pl.col("artists")],
        how="inner"
    ).sort("rank")
    #.with_columns((pl.col("title")).alias("track_name")).with_columns((pl.col("artist")).alias("artists"))

    combined = combined.join(
        billboard_df.select("rank", "title", "artist"),
        on="rank",
        how="inner"
    ).drop(["title", "artist"]).with_columns(
        (pl.col("title_right")
    ).alias("track_name")).with_columns((pl.col("artist_right")).alias("artists")).rename({
        "title_right": "title",
        "artist_right": "artist"
    })

    return combined


def compare_billboard_itunes_overlap(billboard_df: pl.DataFrame, itunes_df: pl.DataFrame, spotify_df: pl.DataFrame) -> pl.DataFrame:

    # Rename Billboard columns to billboard_rank, billboard_title, billboard_artist
    billboard_df = billboard_df.rename({
        "rank": "billboard_rank",
        "title": "billboard_title",
        "artist": "billboard_artist"
    })

    # Rename iTunes columns to itunes_rank, itunes_title, itunes_artist
    itunes_df = itunes_df.rename({
        "rank": "itunes_rank",
        "title": "itunes_title",
        "artist": "itunes_artist"
    })

    # Inner join Billboard and iTunes on normalized title and artist
    joined = billboard_df.join(
        itunes_df,
        left_on=[pl.col("billboard_title").map_elements(normalize_artist_name), pl.col("billboard_artist").map_elements(normalize_artist_name)],
        right_on=[pl.col("itunes_title").map_elements(normalize_artist_name), pl.col("itunes_artist").map_elements(normalize_artist_name)],
        how="inner"
    )

    # Prepare and normalize Spotify data (explode artists if needed)
    spotify_df = spotify_df.explode("artists")

    # Join the overlap with Spotify to get full metadata
    joined = joined.join(
        spotify_df,
        left_on=[pl.col("billboard_title").map_elements(normalize_artist_name), pl.col("billboard_artist").map_elements(normalize_artist_name)],
        right_on=[pl.col("track_name").map_elements(normalize_artist_name), pl.col("artists").map_elements(normalize_artist_name)],
        how="inner"
    ).select([
        "billboard_rank", "itunes_rank", "billboard_title", "billboard_artist",
        "last_week_rank", "peak_rank", "weeks_on_chart", "track_id", "track_name", "artists",
        "album_name", "popularity", "track_genre"
    ]).sort("billboard_rank")

    return joined


def get_billboard_songs_by_genre(
    billboard_df: pl.DataFrame,
    spotify_df: pl.DataFrame,
    genre: str
) -> pl.DataFrame:

    # First use get_billboard_songs_in_spotify() to match Billboard with Spotify
    billboard_in_spotify_df = get_billboard_songs_in_spotify(billboard_df, spotify_df)

    # Normalize the input genre parameter
    genre = normalize_artist_name(genre)

    billboard_in_spotify_df = billboard_in_spotify_df.explode("track_genre").filter(
        (pl.col('track_genre').map_elements(normalize_artist_name) == genre)
    ).sort("rank")
    
    return billboard_in_spotify_df
