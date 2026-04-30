# backend/modeling.py
import numpy as np
import pandas as pd
from itertools import combinations
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from sklearn.model_selection import cross_val_score, RandomizedSearchCV
from sklearn.cluster import KMeans


def build_genre_matrix(items: list[dict]):
    mlb = MultiLabelBinarizer()
    matrix = mlb.fit_transform([item["genres"] for item in items])
    return matrix, mlb.classes_, mlb


def run_feature_engineering(items: list[dict]):
    genre_matrix, genre_classes, mlb = build_genre_matrix(items)

    # top-N genres to keep interactions manageable
    TOP_N = min(30, genre_matrix.shape[1])
    top_indices = np.argsort(genre_matrix.sum(axis=0))[::-1][:TOP_N]
    top_names = genre_classes[top_indices]
    top_matrix = genre_matrix[:, top_indices]

    # pairwise AND interactions
    interaction_cols, interaction_names = [], []
    for i, j in combinations(range(TOP_N), 2):
        interaction = top_matrix[:, i] & top_matrix[:, j]
        if interaction.sum() >= max(2, len(items) // 10):
            interaction_cols.append(interaction)
            interaction_names.append(f"{top_names[i]}+{top_names[j]}")

    if not interaction_cols:
        return {
            "original_feature_count": int(genre_matrix.shape[1]),
            "interaction_feature_count": 0,
            "total_feature_count": int(genre_matrix.shape[1]),
            "top_interactions": [],
            "accuracy_original": None,
            "accuracy_engineered": None,
            "note": "Not enough genre overlap between items to generate interactions."
        }

    interaction_matrix = np.column_stack(interaction_cols)
    genre_matrix_engineered = np.hstack([genre_matrix, interaction_matrix])

    # interaction frequency -> how many artists share each combo
    interaction_freq = interaction_matrix.sum(axis=0).tolist()
    top_interactions = sorted(
        zip(interaction_names, interaction_freq),
        key=lambda x: -x[1]
    )[:10]

    # if enough items, compare accuracy with/without interactions
    accuracy_original = accuracy_engineered = None
    if len(items) >= 6:
        labels = KMeans(
            n_clusters=min(3, len(items) - 1), random_state=42, n_init=10
        ).fit_predict(genre_matrix)

        rf = RandomForestClassifier(n_estimators=50, random_state=42)
        accuracy_original = float(
            cross_val_score(rf, genre_matrix, labels, cv=3, scoring='accuracy').mean()
        )
        accuracy_engineered = float(
            cross_val_score(rf, genre_matrix_engineered, labels, cv=3, scoring='accuracy').mean()
        )

    return {
        "original_feature_count": int(genre_matrix.shape[1]),
        "interaction_feature_count": int(interaction_matrix.shape[1]),
        "total_feature_count": int(genre_matrix_engineered.shape[1]),
        "top_interactions": [
            {"name": name, "artist_count": int(count)}
            for name, count in top_interactions
        ],
        "accuracy_original": round(accuracy_original, 3) if accuracy_original else None,
        "accuracy_engineered": round(accuracy_engineered, 3) if accuracy_engineered else None,
    }


def run_ensemble(items: list[dict]):
    genre_matrix, genre_classes, _ = build_genre_matrix(items)

    if len(items) < 6:
        return {"error": "Add at least 6 items to run ensemble comparison."}

    n_clusters = min(3, len(items) - 1)
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(genre_matrix)

    models = {
        "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=42),
        "Gradient Boosting":   GradientBoostingClassifier(n_estimators=100, random_state=42),
        "Logistic Regression": LogisticRegression(max_iter=500, random_state=42),
    }

    results = {}
    fitted = {}
    for name, model in models.items():
        scores = cross_val_score(model, genre_matrix, labels, cv=3, scoring='accuracy')
        results[name] = {
            "mean_accuracy": round(float(scores.mean()), 3),
            "std": round(float(scores.std()), 3),
        }
        model.fit(genre_matrix, labels)
        fitted[name] = model

    # voting ensemble
    ensemble = VotingClassifier(
        estimators=[
            ("rf",  RandomForestClassifier(n_estimators=100, random_state=42)),
            ("gb",  GradientBoostingClassifier(n_estimators=100, random_state=42)),
            ("lr",  LogisticRegression(max_iter=500, random_state=42)),
        ],
        voting="soft"
    )
    ensemble_scores = cross_val_score(ensemble, genre_matrix, labels, cv=3, scoring='accuracy')
    results["Voting Ensemble"] = {
        "mean_accuracy": round(float(ensemble_scores.mean()), 3),
        "std": round(float(ensemble_scores.std()), 3),
    }

    best = max(results, key=lambda k: results[k]["mean_accuracy"])

    return {
        "model_comparison": [
            {"model": k, **v} for k, v in results.items()
        ],
        "best_model": best,
        "n_clusters": n_clusters,
        "n_items": len(items),
    }


def run_feature_importance(items: list[dict]):
    genre_matrix, genre_classes, _ = build_genre_matrix(items)

    if len(items) < 4:
        return {"error": "Add at least 4 items to run feature importance."}

    n_clusters = min(3, len(items) - 1)
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(genre_matrix)

    # RF feature importances
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(genre_matrix, labels)

    importances = [
        {"genre": genre_classes[i], "importance": round(float(rf.feature_importances_[i]), 4)}
        for i in np.argsort(rf.feature_importances_)[::-1][:15]
        if rf.feature_importances_[i] > 0
    ]

    # PCA feature selection: how many components explain 90% variance
    if genre_matrix.shape[1] >= 2:
        pca = PCA(random_state=42)
        pca.fit(genre_matrix)
        cumvar = np.cumsum(pca.explained_variance_ratio_)
        n_components_90 = int(np.searchsorted(cumvar, 0.90)) + 1
        variance_by_component = [
            {"component": i + 1, "variance_explained": round(float(v), 4)}
            for i, v in enumerate(pca.explained_variance_ratio_[:10])
        ]
    else:
        n_components_90 = 1
        variance_by_component = []

    # accuracy: all features vs top-k PCA features
    accuracy_full = float(
        cross_val_score(
            RandomForestClassifier(n_estimators=50, random_state=42),
            genre_matrix, labels, cv=min(3, len(items))
        ).mean()
    )

    n_comp = min(n_components_90, genre_matrix.shape[0] - 1, genre_matrix.shape[1] - 1)
    pca_reduced = PCA(n_components=max(1, n_comp), random_state=42).fit_transform(genre_matrix)
    accuracy_pca = float(
        cross_val_score(
            RandomForestClassifier(n_estimators=50, random_state=42),
            pca_reduced, labels, cv=min(3, len(items))
        ).mean()
    )

    return {
        "top_genres_by_importance": importances,
        "pca_components_for_90pct_variance": n_components_90,
        "total_genre_features": int(genre_matrix.shape[1]),
        "variance_by_component": variance_by_component,
        "accuracy_full_features": round(accuracy_full, 3),
        "accuracy_pca_reduced": round(accuracy_pca, 3),
    }