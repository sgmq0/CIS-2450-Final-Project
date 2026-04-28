from typing import Optional
import kagglehub
import os
import shutil
import polars as pl


def _data_path(relative_path: str, homework_dir: Optional[str] = None) -> str:
    """
    Resolve a data file path: try homework_X/data/relative_path if that directory
    exists, otherwise data/relative_path. Single place to change path logic.
    """
    if homework_dir and os.path.exists(homework_dir + "/"):
        return os.path.join(homework_dir, "data", relative_path)
    return os.path.join("data", relative_path)


def get_spotify_dataset() -> str:
    """
    Download the dataset from Kaggle if it doesn't already exist locally
    """
    PATH = _data_path("spotify-tracks-dataset.csv", "homework-0")

    if not os.path.exists(PATH):
        path = kagglehub.dataset_download("maharshipandya/-spotify-tracks-dataset")
        shutil.copy(os.path.join(path, "dataset.csv"), PATH)

    return PATH


def load_social_dataset() -> pl.DataFrame:
    """Download the social dataset from Kaggle if it doesn't already exist locally."""
    PATH = _data_path("soc-Epinions1.txt", "homework-1")

    if not os.path.exists(PATH):
        path = kagglehub.dataset_download(
            "wolfram77/graphs-social",
            "soc-Epinions1.txt"
        )
        shutil.copy(os.path.join(path), PATH)

    df = pl.read_csv(PATH, separator="\t", has_header=False, skip_rows=4, encoding="utf8-lossy", infer_schema_length=0, truncate_ragged_lines=True)

    if len(df.columns) >= 2:
        df = df.rename({df.columns[0]: "src", df.columns[1]: "dst"})

    return df


def load_users_dataset() -> pl.DataFrame:
    """Load the users dataset."""
    PATH = _data_path("users.csv", "homework-1")

    if not os.path.exists(PATH):
        raise FileNotFoundError(f"Users dataset not found at {PATH}")

    return pl.read_csv(PATH)

def load_spotify_data(limit: int = 1000) -> Optional[pl.DataFrame]:
    """Load the Spotify dataset sorted by popularity (descending)."""
    data_path = get_spotify_dataset()
    df = pl.read_csv(data_path)
    if 'popularity' in df.columns:
        df = df.with_columns(pl.col('popularity').cast(pl.Int64))
    df = df.sort('popularity', descending=True)
    return df.head(limit) if limit is not None else df


def load_song_id_mapping() -> pl.DataFrame:
    """Load the mapping from social network song IDs (1000+) to Spotify track IDs."""
    PATH = _data_path("song_mapping.csv", "homework-1")

    if os.path.exists(PATH):
        return pl.read_csv(PATH)
    raise FileNotFoundError(f"Song ID mapping not found at {PATH}. Please generate it first.")


def load_preferences_data(limit: int = 1000) -> Optional[pl.DataFrame]:
    """Load user preferences data from CSV."""
    PATH = _data_path("preferences_data.csv", "homework-1")

    if os.path.exists(PATH):
        df = pl.read_csv(PATH)
        return df.head(limit) if limit is not None else df

    raise FileNotFoundError(f"Preferences dataset not found at {PATH}. Please generate it first.")