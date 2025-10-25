#!/usr/bin/env python3
"""
Cinema Data Analysis - ENHANCED with Keywords & Deep Dive
"""

import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import numpy as np
import pandas as pd
import warnings
warnings.f
from scipy import stats as sp_stats

try:
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

WATCHLIST_CANDIDATES = [
    Path("data/Watched.csv"),
    Path("data/data/Watched.csv"),
    Path("data/Watched_enriched.csv"),
    Path("data/data/Watched_enriched.csv"),
    Path("data/enriched_movies.csv"),
    Path("data/data/enriched_movies.csv"),
]

PEOPLE_CANDIDATES = [
    Path("data/enriched_people.csv"),
    Path("data/data/enriched_people.csv"),
]

def resolve_watchlist(cli_arg: Optional[str] = None) -> Path:
    if cli_arg:
        p = Path(cli_arg).expanduser().resolve()
        if p.exists():
            return p
    for p in WATCHLIST_CANDIDATES:
        if p.exists():
            return p.resolve()
    raise FileNotFoundError("Could not find movie data CSV")

def resolve_people() -> Optional[Path]:
    for p in PEOPLE_CANDIDATES:
        if p.exists():
            return p.resolve()
    return None

def load_data(filepath: Optional[str] = None) -> pd.DataFrame:
    if filepath:
        fp = Path(filepath).expanduser().resolve()
    else:
        fp = resolve_watchlist(None)
    df = pd.read_csv(fp, encoding="utf-8-sig")
    print(f"✅ Loaded {len(df)} movies from {fp}")
    return df

def load_people_data() -> Optional[pd.DataFrame]:
    people_path = resolve_people()
    if people_path:
        try:
            df = pd.read_csv(people_path, encoding="utf-8-sig")
            print(f"✅ Loaded {len(df)} people/actors from {people_path}")
            return df
        except Exception as e:
            print(f"⚠️  Could not load people data: {e}")
    return None

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    print("\n🧹 CLEANING DATA...")
    original_count = len(df)
    df = df.drop_duplicates()
    duplicates_removed = original_count - len(df)
    if duplicates_removed > 0:
        print(f"  ✓ Removed {duplicates_removed} duplicates")
    
    column_mapping = {
        'Original Title': 'Title',
        'originalTitle': 'Title',
        'Runtime (mins)': 'Runtime',
        'runtimeMinutes': 'Runtime',
        'startYear': 'Year',
    }
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col not in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    if 'Year' in df.columns:
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    if 'Runtime' in df.columns:
        df['Runtime'] = pd.to_numeric(df['Runtime'], errors='coerce')
    
    print(f"✅ Cleaning complete! {len(df)} records ready\n")
    return df

def pick_col(df, *candidates, default=None):
    for c in candidates:
        if c in df.columns:
            return df[c]
    return pd.Series([pd.NA] * len(df)) if default is None else default

def to_num(s):
    return pd.to_numeric(s, errors="coerce")

def basic_stats(df):
    title = pick_col(df, 'Title', 'Original Title', 'originalTitle')
    runtime = to_num(pick_col(df, 'Runtime', 'Runtime (mins)', 'runtimeMinutes')).fillna(0)
    year = to_num(pick_col(df, 'Year', 'startYear'))
    earliest = int(year.min()) if year.notna().any() else None
    latest = int(year.max()) if year.notna().any() else None
    span = int(latest - earliest) if earliest and latest else None
    return {
        'total_movies': int(len(df)),
        'unique_movies': int(title.nunique(dropna=True)),
        'total_runtime_mins': float(runtime.sum()),
        'total_runtime_hours': round(float(runtime.sum()) / 60, 2),
        'total_runtime_days': round(float(runtime.sum()) / (60 * 24), 2),
        'avg_runtime': round(float(runtime.mean()), 2) if len(runtime) else None,
        'year_range': {'earliest': earliest, 'latest': latest, 'span': span}
    }

def genre_analysis(df):
    gcol = pick_col(df, 'genres_merged', 'Genres', 'genres')
    all_genres = []
    genre_by_movie = {}
    for idx, genres in gcol.dropna().astype(str).items():
        parts = []
        for sep in [',', '|']:
            if sep in genres:
                parts = [p.strip() for p in genres.split(sep)]
                break
        if not parts:
            parts = [genres.strip()]
        valid_parts = [p for p in parts if p and p.lower() != 'nan']
        all_genres.extend(valid_parts)
        genre_by_movie[idx] = valid_parts
    genre_counts = Counter(all_genres)
    genre_combos = Counter()
    for genres in genre_by_movie.values():
        if len(genres) >= 2:
            combo = ' + '.join(sorted(genres[:2]))
            genre_combos[combo] += 1
    return {
        'total_unique_genres': int(len(genre_counts)),
        'top_10_genres': dict(genre_counts.most_common(10)),
        'genre_distribution': dict(genre_counts),
        'top_genre_combinations': dict(genre_combos.most_common(10)),
        'genre_by_movie': genre_by_movie
    }

# NEW: KEYWORD ANALYSIS
def keyword_analysis(df):
    """Analyze keywords from movie metadata"""
    print("\n🔍 ANALYZING KEYWORDS...")
    
    # Try different keyword columns
    keyword_cols = ['tmdb_keywords', 'keywords', 'plot_keywords']
    keyword_col = None
    for col in keyword_cols:
        if col in df.columns:
            keyword_col = col
            break
    
    if not keyword_col:
        print("  ⚠️  No keyword column found")
        return {}
    
    all_keywords = []
    keyword_by_movie = {}
    
    for idx, keywords in df[keyword_col].dropna().astype(str).items():
        # Keywords might be JSON, comma-separated, or pipe-separated
        keywords_list = []
        
        # Try JSON parsing
        if keywords.startswith('[') or keywords.startswith('{'):
            try:
                import json
                parsed = json.loads(keywords)
                if isinstance(parsed, list):
                    keywords_list = [k.get('name', k) if isinstance(k, dict) else str(k) for k in parsed]
                elif isinstance(parsed, dict):
                    keywords_list = list(parsed.values())
            except:
                pass
        
        # Try comma/pipe separation
        if not keywords_list:
            for sep in [',', '|', ';']:
                if sep in keywords:
                    keywords_list = [k.strip() for k in keywords.split(sep)]
                    break
        
        # Clean and add
        keywords_list = [k for k in keywords_list if k and len(k) > 2 and k.lower() != 'nan']
        all_keywords.extend(keywords_list)
        if keywords_list:
            keyword_by_movie[idx] = keywords_list
    
    keyword_counts = Counter(all_keywords)
    
    print(f"  ✓ Found {len(keyword_counts)} unique keywords")
    
    return {
        'total_unique_keywords': len(keyword_counts),
        'top_50_keywords': dict(keyword_counts.most_common(50)),
        'keyword_distribution': dict(keyword_counts),
        'keyword_by_movie': keyword_by_movie
    }

# NEW: DESCRIPTION/OVERVIEW ANALYSIS
def description_analysis(df):
    """Analyze movie descriptions/overviews using TF-IDF"""
    print("\n📝 ANALYZING DESCRIPTIONS...")
    
    # Try different description columns
    desc_cols = ['tmdb_overview', 'overview', 'description', 'plot', 'omdb_plot']
    desc_col = None
    for col in desc_cols:
        if col in df.columns:
            desc_col = col
            break
    
    if not desc_col:
        print("  ⚠️  No description column found")
        return {}
    
    descriptions = df[desc_col].dropna().astype(str)
    
    if len(descriptions) < 10:
        print("  ⚠️  Not enough descriptions for analysis")
        return {}
    
    if not HAS_SKLEARN:
        print("  ⚠️  Install scikit-learn for advanced description analysis")
        # Simple word frequency
        all_words = []
        for desc in descriptions:
            words = desc.lower().split()
            words = [w.strip('.,!?;:') for w in words if len(w) > 4]
            all_words.extend(words)
        
        word_counts = Counter(all_words)
        return {
            'top_description_words': dict(word_counts.most_common(30)),
            'total_words_analyzed': len(all_words)
        }
    
    # Advanced TF-IDF analysis
    try:
        vectorizer = TfidfVectorizer(
            max_features=50,
            stop_words='english',
            min_df=2,
            max_df=0.8
        )
        
        tfidf_matrix = vectorizer.fit_transform(descriptions)
        feature_names = vectorizer.get_feature_names_out()
        
        # Get top terms by TF-IDF score
        tfidf_scores = tfidf_matrix.sum(axis=0).A1
        top_indices = tfidf_scores.argsort()[-30:][::-1]
        top_terms = {feature_names[i]: float(tfidf_scores[i]) for i in top_indices}
        
        print(f"  ✓ Analyzed {len(descriptions)} descriptions")
        
        return {
            'top_tfidf_terms': top_terms,
            'total_descriptions_analyzed': len(descriptions),
            'unique_terms': len(feature_names)
        }
    except Exception as e:
        print(f"  ⚠️  TF-IDF analysis error: {e}")
        return {}

def decade_analysis(df):
    year = to_num(pick_col(df, 'Year', 'startYear'))
    decade = ((year // 10) * 10).dropna().astype(int)
    tmp = df.copy()
    tmp['Decade'] = decade
    decade_counts = tmp['Decade'].value_counts().sort_index()
    runtime = to_num(pick_col(tmp, 'Runtime', 'Runtime (mins)', 'runtimeMinutes')).fillna(0)
    decade_stats = {}
    for d in decade_counts.index:
        mask = tmp['Decade'] == d
        decade_stats[int(d)] = {
            'count': int(mask.sum()),
            'total_runtime_hours': round(float(runtime[mask].sum()) / 60, 2),
        }
    return decade_stats

def director_analysis(df):
    if 'Directors' not in df.columns:
        return {}
    all_directors = []
    for directors in df['Directors'].dropna().astype(str):
        all_directors.extend([d.strip() for d in directors.split(',') if d.strip()])
    director_counts = Counter(all_directors)
    title = pick_col(df, 'Title', 'Original Title', 'originalTitle')
    runtime = to_num(pick_col(df, 'Runtime', 'Runtime (mins)', 'runtimeMinutes')).fillna(0)
    top_directors = {}
    for director, count in director_counts.most_common(20):
        director_movies = df[df['Directors'].str.contains(director, na=False, regex=False)]
        top_directors[director] = {
            'movie_count': int(count),
            'total_runtime_hours': round(float(runtime.loc[director_movies.index].sum()) / 60, 2),
            'movies': title.loc[director_movies.index].dropna().astype(str).tolist()[:10],
        }
    return top_directors

def actor_analysis(people_df, movies_df):
    if people_df is None or len(people_df) == 0:
        return {}
    print("\n🎭 ANALYZING ACTORS...")
    if 'primaryProfession' in people_df.columns:
        actors = people_df[people_df['primaryProfession'].str.contains('actor|actress', case=False, na=False)].copy()
    else:
        actors = people_df.copy()
    print(f"  Found {len(actors)} actors")
    actor_stats = {}
    for idx, row in actors.head(100).iterrows():
        name = row.get('primaryName', 'Unknown')
        birth_year = row.get('birthYear')
        known_for = row.get('knownForTitles', '')
        if pd.notna(known_for):
            known_titles = str(known_for).split(',')
            matches = 0
            if 'Const' in movies_df.columns:
                our_ids = set(movies_df['Const'].dropna().astype(str))
                matches = len([t for t in known_titles if t.strip() in our_ids])
            if matches > 0 or len(actor_stats) < 50:
                actor_stats[name] = {
                    'appearances': matches,
                    'birth_year': int(birth_year) if pd.notna(birth_year) and birth_year != '\\N' else None,
                    'known_for_count': len(known_titles)
                }
    sorted_actors = dict(sorted(actor_stats.items(), key=lambda x: x[1]['appearances'], reverse=True)[:30])
    return {'total_actors': len(actors), 'top_actors': sorted_actors, 'actors_analyzed': len(actor_stats)}

def ml_analysis(df):
    """
    Performs TF-IDF on keywords/overviews and K-Means clustering to find "taste clusters".
    """
    if not HAS_SKLEARN:
        return {'note': 'Install scikit-learn for ML features'}

    print("\n🤖 PERFORMING ML TASTE ANALYSIS...")
    results = {}

    # 1. Prepare text data
    text_data = []
    movie_indices = []

    # Combine keywords and overview for a richer feature set
    keywords_col = pick_col(df, 'tmdb_keywords', 'keywords').fillna("[]")
    overview_col = pick_col(df, 'tmdb_overview', 'overview', 'plot').fillna("")

    for idx, (keywords_json, overview) in enumerate(zip(keywords_col, overview_col)):
        text = ""
        try:
            # Keywords are often stored as a JSON list of strings
            k_list = json.loads(keywords_json)
            if isinstance(k_list, list):
                text += " ".join(k_list)
        except:
            # Fallback if it's just a comma-separated string
            text += str(keywords_json).replace(",", " ")

        text += " " + str(overview)

        if text.strip():
            text_data.append(text)
            movie_indices.append(df.index[idx])

    if len(text_data) < 20:
        print("  ⚠️  Not enough text data (keywords/overviews) for ML analysis.")
        return {'note': 'Not enough data for ML analysis'}

    # 2. Vectorize text using TF-IDF
    print(f"  Vectorizing text from {len(text_data)} movies...")
    try:
        vectorizer = TfidfVectorizer(
            max_features=1000,  # Top 1000 terms
            stop_words='english',
            min_df=5,           # Must appear in at least 5 movies
            max_df=0.7          # Ignore terms in > 70% of movies
        )
        tfidf_matrix = vectorizer.fit_transform(text_data)
        feature_names = vectorizer.get_feature_names_out()
    except Exception as e:
        print(f"  ⚠️  TF-IDF vectorization error: {e}")
        return {'note': f'TF-IDF error: {e}'}

    # 3. K-Means Clustering
    n_clusters = 5  # Let's define 5 core taste clusters
    print(f"  Clustering into {n_clusters} taste clusters...")
    try:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(tfidf_matrix)

        # 4. Analyze and label clusters
        cluster_analysis = {}
        for i in range(n_clusters):
            cluster_mask = (clusters == i)
            cluster_size = int(cluster_mask.sum())

            # Find top terms for this cluster
            cluster_tfidf = tfidf_matrix[cluster_mask]
            top_term_indices = cluster_tfidf.sum(axis=0).A1.argsort()[-10:][::-1]
            top_terms = [feature_names[idx] for idx in top_term_indices]

            # Find top genres in this cluster
            cluster_movie_indices = [movie_indices[j] for j, mask in enumerate(cluster_mask) if mask]
            genre_col = pick_col(df.loc[cluster_movie_indices], 'genres_merged', 'Genres', 'genres').dropna()
            genre_counts = Counter()
            for genres_str in genre_col:
                genre_counts.update([g.strip() for g in str(genres_str).split(',') if g.strip()])
            top_genres = [g for g, _ in genre_counts.most_common(3)]

            cluster_analysis[f"Cluster {i+1}"] = {
                'size': cluster_size,
                'percentage': round((cluster_size / len(text_data)) * 100, 1),
                'top_terms': top_terms,
                'top_genres': top_genres,
                'label': f"{' / '.join(top_genres)}" # A simple label
            }

        results['taste_clusters'] = cluster_analysis
        print(f"  ✓ Created {n_clusters} taste clusters")

    except Exception as e:
        print(f"  ⚠️  K-Means clustering error: {e}")
        return {'note': f'K-Means error: {e}'}

    return results

def prepare_graph_data(df, genres, decades, directors):
    year = to_num(pick_col(df, 'Year', 'startYear')).dropna()
    year_counts = year.value_counts().sort_index()
    runtime = to_num(pick_col(df, 'Runtime', 'Runtime (mins)', 'runtimeMinutes')).dropna()
    runtime_bins = pd.cut(runtime, bins=[0, 60, 90, 120, 150, 180, 600], 
                          labels=['<60', '60-90', '90-120', '120-150', '150-180', '180+'])
    runtime_dist = runtime_bins.value_counts().sort_index()
    return {
        'timeline': {
            'years': [int(y) for y in year_counts.index],
            'counts': [int(c) for c in year_counts.values]
        },
        'runtime_histogram': {
            'bins': [str(b) for b in runtime_dist.index],
            'counts': [int(c) for c in runtime_dist.values]
        }
    }

def generate_insights(df):
    print("\n" + "="*60)
    print("🎬 CINEMA ANALYTICS - ENHANCED with KEYWORDS")
    print("="*60)
    
    stats = basic_stats(df)
    genres = genre_analysis(df)
    keywords = keyword_analysis(df)
    descriptions = description_analysis(df)
    decades = decade_analysis(df)
    directors = director_analysis(df)
    
    people_df = load_people_data()
    actors = {}
    if people_df is not None:
        actors = actor_analysis(people_df, df)
    
    ml_results = ml_analysis(df)
    graph_data = prepare_graph_data(df, genres, decades, directors)
    
    print(f"\n✅ Analysis complete!")
    print(f"📊 {stats['total_movies']} movies")
    print(f"🎭 {genres['total_unique_genres']} genres")
    if keywords:
        print(f"🔍 {keywords.get('total_unique_keywords', 0)} keywords")
    if descriptions:
        print(f"📝 {descriptions.get('total_descriptions_analyzed', 0)} descriptions analyzed")
    print(f"🎬 {len(directors)} directors")
    if actors.get('total_actors'):
        print(f"🌟 {actors['total_actors']} actors")
    
    return {
        'basic_stats': stats,
        'genres': {k: v for k, v in genres.items() if k != 'genre_by_movie'},
        'keywords': keywords if keywords else {},
        'descriptions': descriptions if descriptions else {},
        'decades': decades,
        'directors': directors,
        'actors': actors,
        'ml_insights': ml_results,
        'graph_data': graph_data,
        'generated_at': datetime.now().isoformat()
    }

def save_insights(insights, output_path='data/data/cinema_insights.json'):
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Insights saved to: {output_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str)
    parser.add_argument('--output', type=str, default='data/data/cinema_insights.json')
    parser.add_argument('--no-clean', action='store_true')
    args = parser.parse_args()
    try:
        df = load_data(args.input)
        if not args.no_clean:
            df = clean_data(df)
        insights = generate_insights(df)
        save_insights(insights, args.output)
        print("\n🎉 Dashboard ready!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0

if __name__ == '__main__':
    exit(main())