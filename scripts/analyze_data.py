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
    fp = resolve_watchlist(filepath)
    df = pd.read_csv(fp, encoding="utf-8-sig")
    print(f"Loaded {len(df)} movies from {fp}")
    return df

def basic_stats(df):
    """Calculate basic statistics"""
    stats = {
        'total_movies': len(df),
        'unique_movies': df['Title'].nunique(),
        'total_runtime_mins': df['Runtime (mins)'].sum(),
        'total_runtime_hours': round(df['Runtime (mins)'].sum() / 60, 2),
        'total_runtime_days': round(df['Runtime (mins)'].sum() / (60 * 24), 2),
        'avg_rating': round(df['IMDb Rating'].mean(), 2),
        'median_rating': df['IMDb Rating'].median(),
        'avg_runtime': round(df['Runtime (mins)'].mean(), 2),
        'year_range': {
            'earliest': int(df['Year'].min()),
            'latest': int(df['Year'].max()),
            'span': int(df['Year'].max() - df['Year'].min())
        }
    }
    return stats

def genre_analysis(df):
    """Analyze genre distribution"""
    # Split genres and count
    all_genres = []
    for genres in df['Genres'].dropna():
        all_genres.extend([g.strip() for g in genres.split(',')])
    
    genre_counts = Counter(all_genres)
    
    return {
        'total_unique_genres': len(genre_counts),
        'top_10_genres': dict(genre_counts.most_common(10)),
        'genre_distribution': dict(genre_counts)
    }

def decade_analysis(df):
    """Analyze movies by decade"""
    df['Decade'] = (df['Year'] // 10) * 10
    decade_counts = df['Decade'].value_counts().sort_index()
    
    decade_stats = {}
    for decade in decade_counts.index:
        decade_movies = df[df['Decade'] == decade]
        decade_stats[int(decade)] = {
            'count': int(decade_counts[decade]),
            'avg_rating': round(decade_movies['IMDb Rating'].mean(), 2),
            'total_runtime_hours': round(decade_movies['Runtime (mins)'].sum() / 60, 2)
        }
    
    return decade_stats

def director_analysis(df):
    """Analyze most-watched directors"""
    # Split directors
    all_directors = []
    for directors in df['Directors'].dropna():
        all_directors.extend([d.strip() for d in directors.split(',')])
    
    director_counts = Counter(all_directors)
    
    # Get detailed stats for top directors
    top_directors = {}
    for director, count in director_counts.most_common(15):
        director_movies = df[df['Directors'].str.contains(director, na=False)]
        top_directors[director] = {
            'movie_count': count,
            'avg_rating': round(director_movies['IMDb Rating'].mean(), 2),
            'total_runtime_hours': round(director_movies['Runtime (mins)'].sum() / 60, 2),
            'movies': director_movies['Title'].tolist()
        }
    
    return top_directors

def rating_distribution(df):
    """Analyze rating distribution"""
    rating_bins = pd.cut(df['IMDb Rating'], bins=[0, 5, 6, 7, 8, 9, 10], 
                        labels=['0-5', '5-6', '6-7', '7-8', '8-9', '9-10'])
    
    distribution = rating_bins.value_counts().sort_index()
    
    return {
        'distribution': dict(distribution),
        'highest_rated': {
            'title': df.loc[df['IMDb Rating'].idxmax(), 'Title'],
            'rating': df['IMDb Rating'].max(),
            'year': int(df.loc[df['IMDb Rating'].idxmax(), 'Year'])
        },
        'movies_above_8': len(df[df['IMDb Rating'] >= 8.0]),
        'percentage_above_8': round(len(df[df['IMDb Rating'] >= 8.0]) / len(df) * 100, 2)
    }

def yearly_watching_pattern(df):
    """Analyze watching patterns over years"""
    df['Created_Year'] = pd.to_datetime(df['Created']).dt.year
    
    yearly_counts = df['Created_Year'].value_counts().sort_index()
    
    return {
        'movies_per_year': dict(yearly_counts),
        'most_active_year': {
            'year': int(yearly_counts.idxmax()),
            'count': int(yearly_counts.max())
        },
        'total_years_tracked': len(yearly_counts)
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