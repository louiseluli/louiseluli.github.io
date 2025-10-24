"""
Movie Data Enrichment System
Enriches movie data from IMDb watchlist with:
- IMDb Non-Commercial Datasets
- TMDB (The Movie Database)
- OMDB (Open Movie Database)
- Wikidata
- DoestheDogDie API
"""

import pandas as pd
import requests
import time
import json
import gzip
import os
from urllib.parse import quote
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MovieDataEnricher:
    """Main class for enriching movie data from multiple sources"""
    
    def __init__(self, tmdb_api_key: str, omdb_api_key: str):
        """
        Initialize the enricher with API keys
        
        Args:
            tmdb_api_key: TMDB API key
            omdb_api_key: OMDB API key
        """
        self.tmdb_api_key = tmdb_api_key
        self.omdb_api_key = omdb_api_key
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.omdb_base_url = "http://www.omdbapi.com/"
        self.wikidata_endpoint = "https://query.wikidata.org/sparql"
        self.dtd_base_url = "https://www.doesthedogdie.com/dddsearch"
        
        # Rate limiting
        self.request_delay = 0.25  # 4 requests per second for TMDB
        
    def load_watchlist(self, filepath: str) -> pd.DataFrame:
        """Load the watched movies CSV"""
        logger.info(f"Loading watchlist from {filepath}")
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} movies")
        return df
    
    def download_imdb_datasets(self, output_dir: str = "data/imdb"):
        """Download IMDb non-commercial datasets"""
        logger.info("Downloading IMDb datasets...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        datasets = [
            'title.basics.tsv.gz',
            'title.ratings.tsv.gz',
            'title.crew.tsv.gz',
            'title.principals.tsv.gz',
            'name.basics.tsv.gz'
        ]
        
        base_url = "https://datasets.imdbws.com/"
        
        for dataset in datasets:
            url = base_url + dataset
            filepath = os.path.join(output_dir, dataset)
            
            if os.path.exists(filepath):
                logger.info(f"{dataset} already exists, skipping...")
                continue
                
            logger.info(f"Downloading {dataset}...")
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                logger.info(f"Successfully downloaded {dataset}")
            except Exception as e:
                logger.error(f"Error downloading {dataset}: {e}")
    
    def load_imdb_dataset(self, filepath: str) -> pd.DataFrame:
        """Load and decompress IMDb dataset"""
        logger.info(f"Loading IMDb dataset: {filepath}")
        
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            df = pd.read_csv(f, sep='\t', na_values='\\N', low_memory=False)
        
        logger.info(f"Loaded {len(df)} records from {os.path.basename(filepath)}")
        return df
    
    def enrich_with_imdb(self, df: pd.DataFrame, imdb_dir: str = "data/imdb") -> pd.DataFrame:
        """Enrich movie data with IMDb datasets"""
        logger.info("Enriching with IMDb data...")
        
        # Load IMDb datasets
        basics = self.load_imdb_dataset(os.path.join(imdb_dir, 'title.basics.tsv.gz'))
        ratings = self.load_imdb_dataset(os.path.join(imdb_dir, 'title.ratings.tsv.gz'))
        crew = self.load_imdb_dataset(os.path.join(imdb_dir, 'title.crew.tsv.gz'))
        principals = self.load_imdb_dataset(os.path.join(imdb_dir, 'title.principals.tsv.gz'))
        
        # Merge with basics
        df = df.merge(
            basics[['tconst', 'originalTitle', 'startYear', 'runtimeMinutes', 'genres']],
            left_on='Const',
            right_on='tconst',
            how='left',
            suffixes=('', '_imdb')
        )
        
        # Merge with ratings
        df = df.merge(
            ratings[['tconst', 'averageRating', 'numVotes']],
            on='tconst',
            how='left',
            suffixes=('', '_imdb_detailed')
        )
        
        # Merge with crew
        df = df.merge(
            crew[['tconst', 'directors', 'writers']],
            on='tconst',
            how='left',
            suffixes=('', '_imdb_crew')
        )
        
        logger.info("IMDb enrichment complete")
        return df
    
    def get_tmdb_movie_details(self, imdb_id: str) -> Optional[Dict]:
        """Get movie details from TMDB using IMDb ID"""
        try:
            # Find movie by IMDb ID
            url = f"{self.tmdb_base_url}/find/{imdb_id}"
            params = {
                'api_key': self.tmdb_api_key,
                'external_source': 'imdb_id'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('movie_results'):
                return None
            
            movie_id = data['movie_results'][0]['id']
            
            # Get full movie details
            url = f"{self.tmdb_base_url}/movie/{movie_id}"
            params = {
                'api_key': self.tmdb_api_key,
                'append_to_response': 'keywords,recommendations,similar,images,credits'
            }
            
            time.sleep(self.request_delay)
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.warning(f"Error fetching TMDB data for {imdb_id}: {e}")
            return None
    
    def get_tmdb_genres(self) -> Dict[int, str]:
        """Get TMDB genre list"""
        try:
            url = f"{self.tmdb_base_url}/genre/movie/list"
            params = {'api_key': self.tmdb_api_key}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {genre['id']: genre['name'] for genre in data['genres']}
        except Exception as e:
            logger.error(f"Error fetching TMDB genres: {e}")
            return {}
    
    def merge_genres(self, imdb_genres: str, tmdb_genres: List[Dict]) -> str:
        """Merge IMDb and TMDB genres, avoiding duplicates"""
        genres = set()
        
        # Add IMDb genres
        if pd.notna(imdb_genres):
            for genre in imdb_genres.split(','):
                genre = genre.strip()
                # Normalize Sci-Fi and Science Fiction
                if genre.lower() in ['sci-fi', 'science fiction']:
                    genres.add('Science Fiction')
                else:
                    genres.add(genre)
        
        # Add TMDB genres
        if tmdb_genres:
            for genre in tmdb_genres:
                name = genre['name']
                # Normalize Sci-Fi and Science Fiction
                if name.lower() in ['sci-fi', 'science fiction']:
                    genres.add('Science Fiction')
                else:
                    genres.add(name)
        
        return ', '.join(sorted(genres))
    
    def extract_tmdb_data(self, tmdb_data: Dict) -> Dict:
        """Extract relevant data from TMDB response"""
        if not tmdb_data:
            return {}
        
        # Extract keywords
        keywords = []
        if 'keywords' in tmdb_data and 'keywords' in tmdb_data['keywords']:
            keywords = [kw['name'] for kw in tmdb_data['keywords']['keywords']]
        
        # Extract recommendations
        recommendations = []
        if 'recommendations' in tmdb_data and 'results' in tmdb_data['recommendations']:
            recommendations = [
                {'id': r['id'], 'title': r['title']}
                for r in tmdb_data['recommendations']['results'][:10]
            ]
        
        # Extract similar movies
        similar = []
        if 'similar' in tmdb_data and 'results' in tmdb_data['similar']:
            similar = [
                {'id': r['id'], 'title': r['title']}
                for r in tmdb_data['similar']['results'][:10]
            ]
        
        # Extract images
        images = {
            'backdrops': [],
            'posters': [],
            'logos': []
        }
        if 'images' in tmdb_data:
            if 'backdrops' in tmdb_data['images']:
                images['backdrops'] = [
                    img['file_path'] 
                    for img in tmdb_data['images']['backdrops'][:5]
                ]
            if 'posters' in tmdb_data['images']:
                images['posters'] = [
                    img['file_path'] 
                    for img in tmdb_data['images']['posters'][:5]
                ]
            if 'logos' in tmdb_data['images']:
                images['logos'] = [
                    img['file_path'] 
                    for img in tmdb_data['images']['logos'][:5]
                ]
        
        return {
            'tmdb_id': tmdb_data.get('id'),
            'imdb_id': tmdb_data.get('imdb_id'),
            'tagline': tmdb_data.get('tagline'),
            'genres': tmdb_data.get('genres', []),
            'keywords': keywords,
            'recommendations': recommendations,
            'similar': similar,
            'images': images,
            'overview': tmdb_data.get('overview'),
            'budget': tmdb_data.get('budget'),
            'revenue': tmdb_data.get('revenue'),
            'runtime': tmdb_data.get('runtime')
        }
    
    def enrich_with_tmdb(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich movie data with TMDB"""
        logger.info("Enriching with TMDB data...")
        
        # Initialize new columns
        df['tmdb_id'] = None
        df['tmdb_tagline'] = None
        df['tmdb_keywords'] = None
        df['tmdb_recommendations'] = None
        df['tmdb_similar'] = None
        df['tmdb_images'] = None
        df['genres_merged'] = None
        
        for idx, row in df.iterrows():
            if idx % 50 == 0:
                logger.info(f"Processing movie {idx + 1}/{len(df)}")
            
            imdb_id = row['Const']
            tmdb_data = self.get_tmdb_movie_details(imdb_id)
            
            if tmdb_data:
                extracted = self.extract_tmdb_data(tmdb_data)
                
                df.at[idx, 'tmdb_id'] = extracted.get('tmdb_id')
                df.at[idx, 'tmdb_tagline'] = extracted.get('tagline')
                df.at[idx, 'tmdb_keywords'] = json.dumps(extracted.get('keywords', []))
                df.at[idx, 'tmdb_recommendations'] = json.dumps(extracted.get('recommendations', []))
                df.at[idx, 'tmdb_similar'] = json.dumps(extracted.get('similar', []))
                df.at[idx, 'tmdb_images'] = json.dumps(extracted.get('images', {}))
                
                # Merge genres
                df.at[idx, 'genres_merged'] = self.merge_genres(
                    row.get('Genres', row.get('genres')),
                    extracted.get('genres', [])
                )
        
        logger.info("TMDB enrichment complete")
        return df
    
    def get_omdb_data(self, imdb_id: str) -> Optional[Dict]:
        """Get movie data from OMDB"""
        try:
            params = {
                'apikey': self.omdb_api_key,
                'i': imdb_id,
                'plot': 'full'
            }
            
            response = requests.get(self.omdb_base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('Response') == 'True':
                return {
                    'poster': data.get('Poster'),
                    'plot': data.get('Plot')
                }
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching OMDB data for {imdb_id}: {e}")
            return None
    
    def enrich_with_omdb(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich movie data with OMDB"""
        logger.info("Enriching with OMDB data...")
        
        df['omdb_poster'] = None
        df['omdb_plot'] = None
        
        for idx, row in df.iterrows():
            if idx % 50 == 0:
                logger.info(f"Processing movie {idx + 1}/{len(df)}")
            
            imdb_id = row['Const']
            omdb_data = self.get_omdb_data(imdb_id)
            
            if omdb_data:
                df.at[idx, 'omdb_poster'] = omdb_data.get('poster')
                df.at[idx, 'omdb_plot'] = omdb_data.get('plot')
            
            time.sleep(0.1)  # Rate limiting
        
        logger.info("OMDB enrichment complete")
        return df
    
    def query_wikidata(self, imdb_id: str) -> Optional[Dict]:
        """Query Wikidata for movie information"""
        try:
            query = f"""
            SELECT ?item ?itemLabel ?logoImage ?mainSubject ?mainSubjectLabel 
                   ?filmPoster ?genreLabel ?basedOn ?basedOnLabel 
                   ?setPeriod ?inspiredBy ?inspiredByLabel
            WHERE {{
              ?item wdt:P345 "{imdb_id}".
              OPTIONAL {{ ?item wdt:P154 ?logoImage. }}
              OPTIONAL {{ ?item wdt:P921 ?mainSubject. }}
              OPTIONAL {{ ?item wdt:P3383 ?filmPoster. }}
              OPTIONAL {{ ?item wdt:P136 ?genre. }}
              OPTIONAL {{ ?item wdt:P144 ?basedOn. }}
              OPTIONAL {{ ?item wdt:P2408 ?setPeriod. }}
              OPTIONAL {{ ?item wdt:P941 ?inspiredBy. }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
            """
            
            response = requests.get(
                self.wikidata_endpoint,
                params={'query': query, 'format': 'json'},
                headers={'User-Agent': 'MovieEnricher/1.0'}
            )
            response.raise_for_status()
            
            data = response.json()
            if data['results']['bindings']:
                return data['results']['bindings'][0]
            return None
            
        except Exception as e:
            logger.warning(f"Error querying Wikidata for {imdb_id}: {e}")
            return None
    
    def enrich_with_wikidata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich movie data with Wikidata"""
        logger.info("Enriching with Wikidata...")
        
        df['wiki_logo_image'] = None
        df['wiki_main_subject'] = None
        df['wiki_film_poster'] = None
        df['wiki_based_on'] = None
        df['wiki_set_in_period'] = None
        df['wiki_inspired_by'] = None
        
        for idx, row in df.iterrows():
            if idx % 50 == 0:
                logger.info(f"Processing movie {idx + 1}/{len(df)}")
            
            imdb_id = row['Const']
            wiki_data = self.query_wikidata(imdb_id)
            
            if wiki_data:
                df.at[idx, 'wiki_logo_image'] = wiki_data.get('logoImage', {}).get('value')
                df.at[idx, 'wiki_main_subject'] = wiki_data.get('mainSubjectLabel', {}).get('value')
                df.at[idx, 'wiki_film_poster'] = wiki_data.get('filmPoster', {}).get('value')
                df.at[idx, 'wiki_based_on'] = wiki_data.get('basedOnLabel', {}).get('value')
                df.at[idx, 'wiki_set_in_period'] = wiki_data.get('setPeriod', {}).get('value')
                df.at[idx, 'wiki_inspired_by'] = wiki_data.get('inspiredByLabel', {}).get('value')
            
            time.sleep(0.5)  # Respectful rate limiting for Wikidata
        
        logger.info("Wikidata enrichment complete")
        return df
    
    def save_enriched_data(self, df: pd.DataFrame, output_path: str):
        """Save enriched data to CSV"""
        logger.info(f"Saving enriched data to {output_path}")
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} enriched movies")
    
    def create_summary_report(self, df: pd.DataFrame) -> Dict:
        """Create summary statistics of the enriched dataset"""
        report = {
            'total_movies': len(df),
            'movies_with_tmdb_data': df['tmdb_id'].notna().sum(),
            'movies_with_omdb_data': df['omdb_poster'].notna().sum(),
            'movies_with_wikidata': df['wiki_film_poster'].notna().sum(),
            'unique_genres': len(set(
                genre 
                for genres in df['genres_merged'].dropna() 
                for genre in genres.split(', ')
            )),
            'avg_rating': df['IMDb Rating'].mean(),
            'total_runtime_hours': df['Runtime (mins)'].sum() / 60,
            'year_range': f"{df['Year'].min()} - {df['Year'].max()}"
        }
        return report


def main():
    """Main execution function"""
    # API Keys (should be set as environment variables)
    TMDB_API_KEY = os.getenv('TMDB_API_KEY', 'YOUR_TMDB_API_KEY')
    OMDB_API_KEY = os.getenv('OMDB_API_KEY', 'YOUR_OMDB_API_KEY')
    
    # Initialize enricher
    enricher = MovieDataEnricher(TMDB_API_KEY, OMDB_API_KEY)
    
    # Load watchlist
    df = enricher.load_watchlist('/mnt/project/Watched.csv')
    
    # Download and enrich with IMDb datasets
    enricher.download_imdb_datasets()
    df = enricher.enrich_with_imdb(df)
    
    # Enrich with TMDB (sample first 50 for demo)
    df_sample = df.head(50).copy()
    df_enriched = enricher.enrich_with_tmdb(df_sample)
    
    # Enrich with OMDB
    df_enriched = enricher.enrich_with_omdb(df_enriched)
    
    # Enrich with Wikidata
    df_enriched = enricher.enrich_with_wikidata(df_enriched)
    
    # Save enriched data
    enricher.save_enriched_data(df_enriched, 'data/enriched_movies.csv')
    
    # Generate report
    report = enricher.create_summary_report(df_enriched)
    print("\n" + "="*50)
    print("ENRICHMENT SUMMARY REPORT")
    print("="*50)
    for key, value in report.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("="*50)


if __name__ == "__main__":
    main()
