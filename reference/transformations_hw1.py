"""Reference implementations for Homework 1 transformations.
Used by this homework's transformations.py so HW1 logic lives in one place."""

import polars as pl


def transform_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Transform Spotify data by splitting artists, consolidating by track_id,
    and aggregating artists/genres into lists.
    """
    df = df.with_columns(
        pl.col("artists").str.split(";").alias("artists2")
    ).explode("artists2").drop("artists").rename({"artists2": "artists"})

    grouped_df = df.group_by("track_id").agg([
        pl.col("album_name").first(),
        pl.col("track_name").first(),
        pl.col("popularity").first(),
        pl.col("artists").unique().sort(),
        pl.col("track_genre").unique().sort()
    ]).sort("popularity", descending=True)

    return grouped_df


def get_user_friendships(user_df: pl.DataFrame, edges_df: pl.DataFrame) -> pl.DataFrame:
    """Return DataFrame of user friendships with user and friend names."""
    merged_df = edges_df.join(
        user_df,
        left_on="src",
        right_on="user_id",
        how="inner"
    ).rename({"name": "user_name"})

    merged_df = merged_df.join(
        user_df,
        left_on="dst",
        right_on="user_id",
        how="inner"
    ).rename({"name": "friend_name"})

    friendships_df = merged_df.select([
        "src",
        "user_name",
        "friend_name"
    ])

    return friendships_df


def get_user_friend_counts(user_df: pl.DataFrame, edges_df: pl.DataFrame) -> pl.DataFrame:
    """Get friend count for each user, sorted by count (descending)."""
    friend_counts = edges_df.group_by('src').agg(
        pl.col('dst').count().alias('friend_count')
    ).rename({'src': 'user_id'})

    result = user_df.join(
        friend_counts,
        on='user_id',
        how='left'
    )

    result = result.with_columns(
        pl.col('friend_count').fill_null(0)
    )

    return result.sort('friend_count', descending=True)


def get_user_favorite_songs(
    user_id: int,
    social_df: pl.DataFrame,
    song_mapping_df: pl.DataFrame,
    spotify_df: pl.DataFrame
) -> pl.DataFrame:
    """Get favorite songs for a user, sorted by popularity."""
    user_id = int(user_id)
    social_df = social_df.with_columns(
        pl.col('src').cast(pl.Int64),
        pl.col('dst').cast(pl.Int64)
    )
    song_mapping_df = song_mapping_df.with_columns(
        pl.col('social_song_id').cast(pl.Int64)
    )

    user_songs = social_df.filter(
        (pl.col('src') == user_id) & (pl.col('dst') >= 1000)
    )

    if user_songs.height == 0:
        return pl.DataFrame()

    user_songs = user_songs.join(
        song_mapping_df,
        left_on='dst',
        right_on='social_song_id',
        how='inner'
    ).select(['track_id'])

    result = user_songs.join(
        spotify_df,
        on='track_id',
        how='inner'
    )

    return result.sort('popularity', descending=True)


def get_songs_by_genre_and_artist(spotify_df: pl.DataFrame) -> pl.DataFrame:
    """Return hierarchical genre -> artist -> songs structure for browsing."""
    result = spotify_df.explode('track_genre').rename({'track_genre': 'genre'})
    result = result.explode('artists').rename({'artists': 'artist'})

    result = result.select([
        'genre',
        'artist',
        'track_name',
        'track_id',
        'popularity',
        'album_name'
    ]).sort(['genre', 'artist', pl.col('popularity').sort(descending=True)])

    return result


def get_friend_recommendations(
    user_id: int,
    preferences_df: pl.DataFrame,
    social_df: pl.DataFrame,
    spotify_df: pl.DataFrame,
    top_n: int = 10
) -> pl.DataFrame:
    """
    Get song recommendations based on friend listening habits.
    Returns songs friends listen to that the user hasn't, scored by friend_support.
    """
    user_tracks = (
        preferences_df
        .filter(pl.col('user_id') == user_id)
        .select('track_id')
        .unique()
    )

    if user_tracks.height == 0:
        return pl.DataFrame()

    user_friends = (
        social_df
        .filter((pl.col('src') == user_id) & (pl.col('dst') < 1000))
        .select('dst')
        .unique()
    )

    if user_friends.height == 0:
        return pl.DataFrame()

    friend_tracks = (
        preferences_df
        .join(user_friends, left_on='user_id', right_on='dst', how='inner')
        .select(['user_id', 'track_id'])
    )

    candidate_tracks = friend_tracks.join(
        user_tracks,
        on='track_id',
        how='anti'
    )

    if candidate_tracks.height == 0:
        return pl.DataFrame()

    scored_tracks = (
        candidate_tracks
        .group_by('track_id')
        .agg(pl.len().alias('friend_support'))
    )

    recommendations = (
        scored_tracks
        .join(spotify_df, on='track_id', how='inner')
        .sort(['friend_support', 'popularity'], descending=True)
        .head(top_n)
    )

    return recommendations


def get_top_artists_by_friends(
    user_id: int,
    preferences_df: pl.DataFrame,
    social_df: pl.DataFrame,
    top_n: int = 10
) -> pl.DataFrame:
    """Get top artists among a user's friends using SQL."""
    ctx = pl.SQLContext(
        social_edges=social_df,
        preferences=preferences_df
    )

    query = f"""
    WITH friend_listening AS (
        SELECT
            se.dst AS friend_id,
            p.artists AS artist,
            p.track_id
        FROM social_edges se
        JOIN preferences p ON se.dst = p.user_id
        WHERE se.src = {user_id}
          AND se.dst < 1000
    )
    SELECT
        artist,
        COUNT(DISTINCT track_id) AS tracks_count,
        COUNT(DISTINCT friend_id) AS friend_count
    FROM friend_listening
    GROUP BY artist
    ORDER BY tracks_count DESC, friend_count DESC
    LIMIT {top_n}
    """

    result = ctx.execute(query).collect()
    return result


def get_genre_overlap_between_users(
    preferences_df: pl.DataFrame,
    users_df: pl.DataFrame,
    min_shared_genres: int = 3
) -> pl.DataFrame:
    """Find user pairs who share at least min_shared_genres common genres."""
    ctx = pl.SQLContext(
        preferences=preferences_df,
        users=users_df
    )

    query = f"""
    WITH user_genres AS (
        SELECT DISTINCT user_id, track_genre AS genre
        FROM preferences
    )
    SELECT
        ug1.user_id AS user1_id,
        u1.name AS user1_name,
        ug2.user_id AS user2_id,
        u2.name AS user2_name,
        ug1.genre AS shared_genre
    FROM user_genres ug1
    JOIN user_genres ug2 ON ug1.genre = ug2.genre
    JOIN users u1 ON ug1.user_id = u1.user_id
    JOIN users u2 ON ug2.user_id = u2.user_id
    WHERE ug1.user_id < ug2.user_id
    """

    base_result = ctx.execute(query).collect()

    if base_result.height == 0:
        return pl.DataFrame()

    result = (
        base_result
        .group_by(['user1_id', 'user1_name', 'user2_id', 'user2_name'])
        .agg([
            pl.col('shared_genre').n_unique().alias('shared_genres'),
            pl.col('shared_genre').unique().sort().alias('genres_list')
        ])
        .filter(pl.col('shared_genres') >= min_shared_genres)
        .sort('shared_genres', descending=True)
    )

    return result


def get_popular_songs_among_friends(
    user_id: int,
    social_df: pl.DataFrame,
    song_mapping_df: pl.DataFrame,
    spotify_df: pl.DataFrame
) -> pl.DataFrame:
    """Return popular songs among a user's friends, ranked by friend_like_count."""
    friends = social_df.filter(
        (pl.col("src") == user_id) & (pl.col("dst") < 1000)
    ).select(
        pl.col("dst").alias("friend_id")
    )

    friends_songs = friends.join(
        social_df,
        left_on="friend_id",
        right_on="src",
        how="inner"
    ).filter(
        pl.col("dst") >= 1000
    ).select(
        pl.col("dst").alias("social_song_id"),
        pl.col("friend_id")
    )

    song_counts = friends_songs.group_by("social_song_id").agg(
        pl.col("friend_id").n_unique().alias("friend_like_count")
    )

    result = (
        song_counts
        .join(song_mapping_df, on="social_song_id", how="inner")
        .join(spotify_df, on="track_id", how="inner")
        .select([
            "artists",
            "album_name",
            "track_name",
            "friend_like_count",
            "popularity"
        ])
        .sort(
            ["friend_like_count", "popularity"],
            descending=[True, True]
        )
    )

    return result


def get_top_genres_among_friends(
    user_id: int,
    social_df: pl.DataFrame,
    song_mapping_df: pl.DataFrame,
    spotify_df: pl.DataFrame,
    limit: int = 10
) -> pl.DataFrame:
    """Return top genres among a user's friends using SQL."""
    ctx = pl.SQLContext(
        social=social_df,
        song_mapping=song_mapping_df,
        songs=spotify_df
    )

    query = f"""
    WITH friends AS (
        SELECT dst AS friend_id
        FROM social
        WHERE src = {int(user_id)}
          AND dst < 1000
    ),
    friend_songs AS (
        SELECT f.friend_id, s.dst AS social_song_id
        FROM friends f
        JOIN social s
            ON f.friend_id = s.src
        WHERE s.dst >= 1000
    ),
    friend_tracks AS (
        SELECT fs.friend_id, sm.track_id
        FROM friend_songs fs
        JOIN song_mapping sm
            ON fs.social_song_id = sm.social_song_id
    ),
    songs_genres AS (
        SELECT DISTINCT track_id, track_genre
        FROM songs
    ),
    friend_genres AS (
        SELECT DISTINCT ft.friend_id, sg.track_genre
        FROM friend_tracks ft
        JOIN songs_genres sg
            ON ft.track_id = sg.track_id
    )
    SELECT
        track_genre,
        COUNT(*) AS friend_count
    FROM friend_genres
    GROUP BY track_genre
    ORDER BY friend_count DESC
    LIMIT {int(limit)}
    """

    return ctx.execute(query).collect()


def get_top_songs_per_genre(
    social_df: pl.DataFrame,
    song_mapping_df: pl.DataFrame,
    spotify_df: pl.DataFrame,
    track_genre: str,
    limit: int = 10
) -> pl.DataFrame:
    """Return top songs for a genre, ranked by like_count then popularity."""
    ctx = pl.SQLContext(
        social=social_df,
        song_mapping=song_mapping_df,
        songs=spotify_df
    )

    query = f"""
    WITH song_likes AS (
        SELECT
            sm.track_id,
            COUNT(*) AS like_count
        FROM social s
        JOIN song_mapping sm
            ON s.dst = sm.social_song_id
        WHERE s.dst >= 1000
        GROUP BY sm.track_id
    ),
    songs_dedup AS (
        SELECT
            track_id,
            track_genre,
            MAX(track_name) AS track_name,
            MAX(artists) AS artists,
            MAX(popularity) AS popularity
        FROM songs
        GROUP BY track_id, track_genre
    ),
    ranked AS (
        SELECT
            sd.track_genre,
            sd.track_id,
            sd.track_name,
            sd.artists,
            sd.popularity,
            sl.like_count,
            ROW_NUMBER() OVER (
                PARTITION BY sd.track_genre
                ORDER BY sl.like_count DESC, sd.popularity DESC
            ) AS genre_rank
        FROM songs_dedup sd
        JOIN song_likes sl
            ON sd.track_id = sl.track_id
    )
    SELECT
        track_genre,
        ranked.track_id,
        track_name,
        artists,
        popularity,
        like_count,
        genre_rank
    FROM ranked
    WHERE track_genre = '{track_genre}'
      AND genre_rank <= {int(limit)}
    ORDER BY genre_rank
    """

    return ctx.execute(query).collect()
