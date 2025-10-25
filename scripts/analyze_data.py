#!/usr/bin/env python3
"""
Cinema Data Analysis
Generate insights and statistics from watched movies
"""

import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional
import numpy as np

import pandas as pd

WATCHLIST_CANDIDATES = [
    Path("data/Watched.csv"),
    Path("pages/Watched.csv"),
    Path("/mnt/data/Watched.csv"),
    Path("/mnt/project/Watched.csv"),
]

def resolve_watchlist(cli_arg: Optional[str] = None) -> Path:
    if cli_arg:
        p = Path(cli_arg).expanduser().resolve()
        if p.exists():
            return p
        raise FileNotFoundError(f"Watchlist not found at: {p}")
    for p in WATCHLIST_CANDIDATES:
        if p.exists():
            return p.resolve()
    tried = "\n  - " + "\n  - ".join(str(p) for p in WATCHLIST_CANDIDATES)
    raise FileNotFoundError("Could not find Watched.csv. I looked in:" + tried)

def load_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Prefer enriched CSV if present; otherwise fall back to the watchlist.
    """
    enriched = Path("data/Watched_enriched.csv")
    if filepath:
        fp = Path(filepath).expanduser().resolve()
    elif enriched.exists():
        fp = enriched
    else:
        fp = resolve_watchlist(None)

    df = pd.read_csv(fp, encoding="utf-8-sig")
    print(f"Loaded {len(df)} movies from {fp}")
    return df


# ---------- NEW: schema-compat helpers ----------

def pick_col(df: pd.DataFrame, *candidates, default=None):
    """
    Return the first existing column among candidates; otherwise default (Series of NaNs if default is None).
    """
    for c in candidates:
        if c in df.columns:
            return df[c]
    if default is None:
        return pd.Series([pd.NA] * len(df))
    return default

def to_num(s: pd.Series, allow_int=True):
    """
    Safely coerce a series (possibly strings) to numeric.
    """
    x = pd.to_numeric(s, errors="coerce")
    return x

def to_date(s: pd.Series):
    return pd.to_datetime(s, errors="coerce")


def basic_stats(df):
    """Calculate basic statistics (compatible with raw and enriched schemas)"""
    title = pick_col(df, 'Title', 'Original Title', 'originalTitle')
    runtime = to_num(pick_col(df, 'Runtime (mins)', 'runtimeMinutes')).fillna(0)
    rating = to_num(pick_col(df, 'IMDb Rating', 'averageRating'))
    year = to_num(pick_col(df, 'Year', 'startYear'))

    earliest = int(year.min()) if year.notna().any() else None
    latest = int(year.max()) if year.notna().any() else None
    span = int(latest - earliest) if earliest is not None and latest is not None else None

    stats = {
        'total_movies': int(len(df)),
        'unique_movies': int(title.nunique(dropna=True)),
        'total_runtime_mins': float(runtime.sum()),
        'total_runtime_hours': round(float(runtime.sum()) / 60, 2),
        'total_runtime_days': round(float(runtime.sum()) / (60 * 24), 2),
        'avg_rating': round(float(rating.mean()), 2) if rating.notna().any() else None,
        'median_rating': float(rating.median()) if rating.notna().any() else None,
        'avg_runtime': round(float(runtime.mean()), 2) if len(runtime) else None,
        'year_range': {
            'earliest': earliest,
            'latest': latest,
            'span': span
        }
    }
    return stats


def genre_analysis(df):
    """Analyze genre distribution (supports Genres, genres, genres_merged)"""
    gcol = pick_col(df, 'genres_merged', 'Genres', 'genres')
    all_genres = []
    for genres in gcol.dropna().astype(str):
        # support comma or pipe separators
        parts = []
        for sep in [',', '|']:
            if sep in genres:
                parts = [p.strip() for p in genres.split(sep)]
                break
        if not parts:
            parts = [genres.strip()]
        all_genres.extend([p for p in parts if p])

    genre_counts = Counter(all_genres)
    return {
        'total_unique_genres': int(len(genre_counts)),
        'top_10_genres': dict(genre_counts.most_common(10)),
        'genre_distribution': dict(genre_counts)
    }


def decade_analysis(df):
    """Analyze movies by decade (works with Year/startYear)"""
    year = to_num(pick_col(df, 'Year', 'startYear'))
    decade = ((year // 10) * 10).dropna().astype(int)
    tmp = df.copy()
    tmp['Decade'] = decade
    decade_counts = tmp['Decade'].value_counts().sort_index()

    decade_stats = {}
    rating = to_num(pick_col(tmp, 'IMDb Rating', 'averageRating'))
    runtime = to_num(pick_col(tmp, 'Runtime (mins)', 'runtimeMinutes')).fillna(0)

    for d in decade_counts.index:
        mask = tmp['Decade'] == d
        decade_stats[int(d)] = {
            'count': int(mask.sum()),
            'avg_rating': round(float(rating[mask].mean()), 2) if rating[mask].notna().any() else None,
            'total_runtime_hours': round(float(runtime[mask].sum()) / 60, 2),
        }
    return decade_stats


def director_analysis(df):
    """Analyze most-watched directors (only if name column exists)"""
    if 'Directors' not in df.columns:
        return {}  # IMDb crew 'directors' are nconsts; we skip that case.

    all_directors = []
    for directors in df['Directors'].dropna().astype(str):
        all_directors.extend([d.strip() for d in directors.split(',') if d.strip()])

    director_counts = Counter(all_directors)

    # detailed stats for top directors
    title = pick_col(df, 'Title', 'Original Title', 'originalTitle')
    rating = to_num(pick_col(df, 'IMDb Rating', 'averageRating'))
    runtime = to_num(pick_col(df, 'Runtime (mins)', 'runtimeMinutes')).fillna(0)

    top_directors = {}
    for director, count in director_counts.most_common(15):
        director_movies = df[df['Directors'].str.contains(director, na=False)]
        top_directors[director] = {
            'movie_count': int(count),
            'avg_rating': round(float(rating.loc[director_movies.index].mean()), 2) if rating.loc[director_movies.index].notna().any() else None,
            'total_runtime_hours': round(float(runtime.loc[director_movies.index].sum()) / 60, 2),
            'movies': title.loc[director_movies.index].dropna().astype(str).tolist(),
        }
    return top_directors


def rating_distribution(df):
    """Analyze rating distribution (works with IMDb Rating or averageRating)"""
    rating = to_num(pick_col(df, 'IMDb Rating', 'averageRating'))
    title = pick_col(df, 'Title', 'Original Title', 'originalTitle')
    year = to_num(pick_col(df, 'Year', 'startYear'))

    rating_bins = pd.cut(rating, bins=[0, 5, 6, 7, 8, 9, 10],
                         labels=['0-5', '5-6', '6-7', '7-8', '8-9', '9-10'])
    distribution = rating_bins.value_counts().sort_index()

    highest_title = None
    highest_rating = None
    highest_year = None
    if rating.notna().any():
        idx = rating.idxmax()
        highest_title = str(title.loc[idx]) if pd.notna(title.loc[idx]) else None
        highest_rating = float(rating.max())
        highest_year = int(year.loc[idx]) if pd.notna(year.loc[idx]) else None

    above_8 = rating[rating >= 8.0]
    return {
        'distribution': {str(k): int(v) for k, v in distribution.items()},
        'highest_rated': {
            'title': highest_title,
            'rating': highest_rating,
            'year': highest_year
        },
        'movies_above_8': int(above_8.notna().sum()),
        'percentage_above_8': round(float(above_8.notna().sum()) / len(df) * 100, 2) if len(df) else 0.0
    }


def yearly_watching_pattern(df):
    """Analyze watching patterns over years using Created/Date Rated/Modified/Release Date"""
    created = to_date(pick_col(df, 'Created'))
    if created.isna().all():
        created = to_date(pick_col(df, 'Date Rated'))
    if created.isna().all():
        created = to_date(pick_col(df, 'Modified'))
    if created.isna().all():
        created = to_date(pick_col(df, 'Release Date'))

    if created.isna().all():
        return {'movies_per_year': {}, 'most_active_year': {'year': None, 'count': 0}, 'total_years_tracked': 0}

    years = created.dt.year.dropna().astype(int)
    yearly_counts = years.value_counts().sort_index()

    most_year = int(yearly_counts.idxmax()) if not yearly_counts.empty else None
    most_count = int(yearly_counts.max()) if not yearly_counts.empty else 0

    return {
        'movies_per_year': {int(k): int(v) for k, v in yearly_counts.items()},
        'most_active_year': {'year': most_year, 'count': most_count},
        'total_years_tracked': int(len(yearly_counts))
    }


def generate_insights(df):
    """Generate comprehensive insights"""
    print("\n" + "="*60)
    print("CINEMA ANALYTICS - COMPREHENSIVE INSIGHTS")
    print("="*60)
    
    # Basic Stats
    print("\n📊 BASIC STATISTICS")
    print("-"*60)
    stats = basic_stats(df)
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"\n{key.replace('_', ' ').title()}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Genre Analysis
    print("\n🎬 GENRE ANALYSIS")
    print("-"*60)
    genres = genre_analysis(df)
    print(f"Total Unique Genres: {genres['total_unique_genres']}")
    print("\nTop 10 Genres:")
    for genre, count in genres['top_10_genres'].items():
        print(f"  {genre}: {count} movies")
    
    # Decade Analysis
    print("\n📅 DECADE BREAKDOWN")
    print("-"*60)
    decades = decade_analysis(df)
    for decade, stats in sorted(decades.items()):
        print(f"\n{decade}s:")
        print(f"  Movies: {stats['count']}")
        print(f"  Avg Rating: {stats['avg_rating']}")
        print(f"  Total Hours: {stats['total_runtime_hours']}")
    
    # Director Analysis
    print("\n🎥 TOP DIRECTORS")
    print("-"*60)
    directors = director_analysis(df)
    for director, stats in list(directors.items())[:10]:
        print(f"\n{director}:")
        print(f"  Movies Watched: {stats['movie_count']}")
        print(f"  Avg Rating: {stats['avg_rating']}")
        print(f"  Total Hours: {stats['total_runtime_hours']}")
    
    # Rating Distribution
    print("\n⭐ RATING DISTRIBUTION")
    print("-"*60)
    ratings = rating_distribution(df)
    for rating_range, count in ratings['distribution'].items():
        print(f"{rating_range}: {count} movies")
    print(f"\nHighest Rated: {ratings['highest_rated']['title']} ({ratings['highest_rated']['rating']})")
    print(f"Movies Rated 8.0+: {ratings['movies_above_8']} ({ratings['percentage_above_8']}%)")
    
    # Watching Patterns
    print("\n📈 WATCHING PATTERNS")
    print("-"*60)
    patterns = yearly_watching_pattern(df)
    print(f"Total Years Tracked: {patterns['total_years_tracked']}")
    print(f"Most Active Year: {patterns['most_active_year']['year']} ({patterns['most_active_year']['count']} movies)")
    
    print("\n" + "="*60)
    
    # Return all data for potential JSON export
    return {
        'basic_stats': stats,
        'genres': genres,
        'decades': decades,
        'directors': directors,
        'ratings': ratings,
        'patterns': patterns,
        'generated_at': datetime.now().isoformat()
    }
    
def _json_default(o):
    # Safely convert NumPy / pandas scalars to native Python types
    if isinstance(o, (np.integer, )):
        return int(o)
    if isinstance(o, (np.floating, )):
        return float(o)
    if isinstance(o, (np.bool_, )):
        return bool(o)
    return str(o)


def save_insights(insights, output_path='data/cinema_insights.json'):
    """Save insights to JSON file"""
    os.makedirs(Path(output_path).parent, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(insights, f, indent=2, ensure_ascii=False, default=_json_default)
    print(f"\n✅ Insights saved to {output_path}")


def main():
    """Main execution"""
    # Load data
    df = load_data()
    
    # Generate insights
    insights = generate_insights(df)
    
    # Save to JSON
    save_insights(insights)
    
    # Additional analysis: Your rated movies
    rated_movies = df[df['Your Rating'].notna()]
    if len(rated_movies) > 0:
        print("\n" + "="*60)
        print("YOUR RATINGS ANALYSIS")
        print("="*60)
        print(f"Movies You Rated: {len(rated_movies)}")
        print(f"Your Average Rating: {rated_movies['Your Rating'].mean():.2f}")
        print(f"Your vs IMDb Avg Difference: {(rated_movies['Your Rating'].mean() - rated_movies['IMDb Rating'].mean()):.2f}")
        
        # Your highest rated
        highest = rated_movies.loc[rated_movies['Your Rating'].idxmax()]
        print(f"\nYour Highest Rated: {highest['Title']} ({highest['Your Rating']})")
        print("="*60)

if __name__ == "__main__":
    main()