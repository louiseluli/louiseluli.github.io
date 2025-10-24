"""
People Data Enrichment System
Enriches data for actors, actresses, and directors from:
- IMDb Non-Commercial Datasets
- TMDB (The Movie Database)
- Wikidata
"""

import pandas as pd
import requests
import time
import json
import gzip
import os
from typing import Dict, List, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PeopleDataEnricher:
    """Enriches data for people (actors, directors, etc.)"""
    
    def __init__(self, tmdb_api_key: str):
        self.tmdb_api_key = tmdb_api_key
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.wikidata_endpoint = "https://query.wikidata.org/sparql"
        self.request_delay = 0.25
        
    def load_imdb_people(self, filepath: str = "data/imdb/name.basics.tsv.gz") -> pd.DataFrame:
        """Load IMDb names dataset"""
        logger.info("Loading IMDb names dataset...")
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            df = pd.read_csv(f, sep='\t', na_values='\\N', low_memory=False)
        logger.info(f"Loaded {len(df)} people from IMDb")
        return df
    
    def extract_people_from_movies(self, movies_df: pd.DataFrame, 
                                   principals_path: str = "data/imdb/title.principals.tsv.gz") -> pd.DataFrame:
        """Extract unique people from movies dataset"""
        logger.info("Extracting people from movies...")
        
        # Load principals
        with gzip.open(principals_path, 'rt', encoding='utf-8') as f:
            principals = pd.read_csv(f, sep='\t', na_values='\\N', low_memory=False)
        
        # Filter for movies in watchlist
        movie_ids = set(movies_df['Const'].values)
        people_in_movies = principals[principals['tconst'].isin(movie_ids)]
        
        # Get unique people
        unique_people = people_in_movies['nconst'].unique()
        logger.info(f"Found {len(unique_people)} unique people in watched movies")
        
        return unique_people
    
    def get_tmdb_person_details(self, imdb_id: str) -> Optional[Dict]:
        """Get person details from TMDB using IMDb ID"""
        try:
            # Find person by IMDb ID
            url = f"{self.tmdb_base_url}/find/{imdb_id}"
            params = {
                'api_key': self.tmdb_api_key,
                'external_source': 'imdb_id'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('person_results'):
                return None
            
            person_id = data['person_results'][0]['id']
            
            # Get full person details
            url = f"{self.tmdb_base_url}/person/{person_id}"
            params = {
                'api_key': self.tmdb_api_key,
                'append_to_response': 'combined_credits,images'
            }
            
            time.sleep(self.request_delay)
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.warning(f"Error fetching TMDB data for {imdb_id}: {e}")
            return None
    
    def extract_tmdb_person_data(self, tmdb_data: Dict) -> Dict:
        """Extract relevant person data from TMDB response"""
        if not tmdb_data:
            return {}
        
        # Gender mapping
        gender_map = {
            0: 'Not set',
            1: 'Female',
            2: 'Male',
            3: 'Non-binary'
        }
        
        # Extract profile images
        images = []
        if 'images' in tmdb_data and 'profiles' in tmdb_data['images']:
            images = [
                img['file_path'] 
                for img in tmdb_data['images']['profiles'][:5]
            ]
        
        # Extract combined credits
        combined_credits = {
            'cast': [],
            'crew': []
        }
        if 'combined_credits' in tmdb_data:
            if 'cast' in tmdb_data['combined_credits']:
                combined_credits['cast'] = [
                    {
                        'title': c.get('title') or c.get('name'),
                        'character': c.get('character'),
                        'id': c.get('id')
                    }
                    for c in tmdb_data['combined_credits']['cast'][:20]
                ]
            if 'crew' in tmdb_data['combined_credits']:
                combined_credits['crew'] = [
                    {
                        'title': c.get('title') or c.get('name'),
                        'job': c.get('job'),
                        'department': c.get('department'),
                        'id': c.get('id')
                    }
                    for c in tmdb_data['combined_credits']['crew'][:20]
                ]
        
        return {
            'tmdb_id': tmdb_data.get('id'),
            'imdb_id': tmdb_data.get('imdb_id'),
            'gender': gender_map.get(tmdb_data.get('gender', 0), 'Not set'),
            'also_known_as': tmdb_data.get('also_known_as', []),
            'biography': tmdb_data.get('biography'),
            'birthday': tmdb_data.get('birthday'),
            'deathday': tmdb_data.get('deathday'),
            'place_of_birth': tmdb_data.get('place_of_birth'),
            'profile_images': images,
            'combined_credits': combined_credits,
            'known_for_department': tmdb_data.get('known_for_department'),
            'popularity': tmdb_data.get('popularity')
        }
    
    def query_wikidata_person(self, imdb_id: str) -> Optional[Dict]:
        """Query Wikidata for person information"""
        try:
            query = f"""
            SELECT ?person ?personLabel ?nickname ?pseudonym ?familyName ?givenName 
                   ?birthName ?languagesSpoken ?nativeLanguage ?child ?father ?mother
                   ?spouse ?causeOfDeath ?mannerOfDeath ?placeOfDeath ?placeOfBirth
                   ?ethnicGroup ?numberOfChildren ?placeOfBurial ?signature ?height
                   ?nominatedFor ?awardReceived ?notableWork ?significantEvent
                   ?namedAfter ?instrument ?medicalCondition ?eyeColor ?religionOrWorldview
                   ?sibling ?hairColor ?politicalParty ?relative ?unmarriedPartner
            WHERE {{
              ?person wdt:P345 "{imdb_id}".
              OPTIONAL {{ ?person wdt:P1449 ?nickname. }}
              OPTIONAL {{ ?person wdt:P742 ?pseudonym. }}
              OPTIONAL {{ ?person wdt:P734 ?familyName. }}
              OPTIONAL {{ ?person wdt:P735 ?givenName. }}
              OPTIONAL {{ ?person wdt:P1477 ?birthName. }}
              OPTIONAL {{ ?person wdt:P1412 ?languagesSpoken. }}
              OPTIONAL {{ ?person wdt:P103 ?nativeLanguage. }}
              OPTIONAL {{ ?person wdt:P40 ?child. }}
              OPTIONAL {{ ?person wdt:P22 ?father. }}
              OPTIONAL {{ ?person wdt:P25 ?mother. }}
              OPTIONAL {{ ?person wdt:P26 ?spouse. }}
              OPTIONAL {{ ?person wdt:P509 ?causeOfDeath. }}
              OPTIONAL {{ ?person wdt:P1196 ?mannerOfDeath. }}
              OPTIONAL {{ ?person wdt:P20 ?placeOfDeath. }}
              OPTIONAL {{ ?person wdt:P19 ?placeOfBirth. }}
              OPTIONAL {{ ?person wdt:P172 ?ethnicGroup. }}
              OPTIONAL {{ ?person wdt:P1971 ?numberOfChildren. }}
              OPTIONAL {{ ?person wdt:P119 ?placeOfBurial. }}
              OPTIONAL {{ ?person wdt:P109 ?signature. }}
              OPTIONAL {{ ?person wdt:P2048 ?height. }}
              OPTIONAL {{ ?person wdt:P1411 ?nominatedFor. }}
              OPTIONAL {{ ?person wdt:P166 ?awardReceived. }}
              OPTIONAL {{ ?person wdt:P800 ?notableWork. }}
              OPTIONAL {{ ?person wdt:P793 ?significantEvent. }}
              OPTIONAL {{ ?person wdt:P138 ?namedAfter. }}
              OPTIONAL {{ ?person wdt:P1303 ?instrument. }}
              OPTIONAL {{ ?person wdt:P1050 ?medicalCondition. }}
              OPTIONAL {{ ?person wdt:P1340 ?eyeColor. }}
              OPTIONAL {{ ?person wdt:P140 ?religionOrWorldview. }}
              OPTIONAL {{ ?person wdt:P3373 ?sibling. }}
              OPTIONAL {{ ?person wdt:P1884 ?hairColor. }}
              OPTIONAL {{ ?person wdt:P102 ?politicalParty. }}
              OPTIONAL {{ ?person wdt:P1038 ?relative. }}
              OPTIONAL {{ ?person wdt:P451 ?unmarriedPartner. }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
            LIMIT 1
            """
            
            response = requests.get(
                self.wikidata_endpoint,
                params={'query': query, 'format': 'json'},
                headers={'User-Agent': 'PeopleEnricher/1.0'}
            )
            response.raise_for_status()
            
            data = response.json()
            if data['results']['bindings']:
                return data['results']['bindings']
            return None
            
        except Exception as e:
            logger.warning(f"Error querying Wikidata for {imdb_id}: {e}")
            return None
    
    def enrich_people_data(self, people_ids: List[str], imdb_people: pd.DataFrame) -> pd.DataFrame:
        """Enrich people data from all sources"""
        logger.info(f"Enriching data for {len(people_ids)} people...")
        
        enriched_data = []
        
        for idx, person_id in enumerate(people_ids):
            if idx % 50 == 0:
                logger.info(f"Processing person {idx + 1}/{len(people_ids)}")
            
            # Get IMDb data
            imdb_data = imdb_people[imdb_people['nconst'] == person_id]
            if imdb_data.empty:
                continue
            
            person_info = {
                'nconst': person_id,
                'imdb_name': imdb_data.iloc[0]['primaryName'],
                'birth_year_imdb': imdb_data.iloc[0].get('birthYear'),
                'death_year_imdb': imdb_data.iloc[0].get('deathYear'),
                'primary_profession': imdb_data.iloc[0].get('primaryProfession'),
                'known_for_titles': imdb_data.iloc[0].get('knownForTitles')
            }
            
            # Get TMDB data
            tmdb_data = self.get_tmdb_person_details(person_id)
            if tmdb_data:
                tmdb_extracted = self.extract_tmdb_person_data(tmdb_data)
                person_info.update({
                    'tmdb_id': tmdb_extracted.get('tmdb_id'),
                    'gender': tmdb_extracted.get('gender'),
                    'also_known_as': json.dumps(tmdb_extracted.get('also_known_as', [])),
                    'biography': tmdb_extracted.get('biography'),
                    'birthday': tmdb_extracted.get('birthday'),
                    'deathday': tmdb_extracted.get('deathday'),
                    'place_of_birth': tmdb_extracted.get('place_of_birth'),
                    'profile_images': json.dumps(tmdb_extracted.get('profile_images', [])),
                    'combined_credits': json.dumps(tmdb_extracted.get('combined_credits', {})),
                    'known_for_department': tmdb_extracted.get('known_for_department'),
                    'popularity': tmdb_extracted.get('popularity')
                })
            
            # Get Wikidata
            wiki_data = self.query_wikidata_person(person_id)
            if wiki_data:
                # Extract first result's values
                first_result = wiki_data[0] if wiki_data else {}
                person_info.update({
                    'wiki_nickname': first_result.get('nickname', {}).get('value'),
                    'wiki_pseudonym': first_result.get('pseudonym', {}).get('value'),
                    'wiki_family_name': first_result.get('familyName', {}).get('value'),
                    'wiki_given_name': first_result.get('givenName', {}).get('value'),
                    'wiki_birth_name': first_result.get('birthName', {}).get('value'),
                    'wiki_ethnic_group': first_result.get('ethnicGroup', {}).get('value'),
                    'wiki_height': first_result.get('height', {}).get('value'),
                    'wiki_eye_color': first_result.get('eyeColor', {}).get('value'),
                    'wiki_hair_color': first_result.get('hairColor', {}).get('value')
                })
            
            enriched_data.append(person_info)
            time.sleep(0.3)  # Rate limiting
        
        df = pd.DataFrame(enriched_data)
        logger.info(f"Enriched data for {len(df)} people")
        return df
    
    def save_enriched_people(self, df: pd.DataFrame, output_path: str):
        """Save enriched people data"""
        logger.info(f"Saving enriched people data to {output_path}")
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} enriched people records")


def main():
    """Main execution function"""
    TMDB_API_KEY = os.getenv('TMDB_API_KEY', 'YOUR_TMDB_API_KEY')
    
    enricher = PeopleDataEnricher(TMDB_API_KEY)
    
    # Load IMDb people dataset
    imdb_people = enricher.load_imdb_people()
    
    # Load movies to extract people
    movies_df = pd.read_csv('/mnt/project/Watched.csv')
    people_ids = enricher.extract_people_from_movies(movies_df)
    
    # Sample first 100 for demo
    people_sample = list(people_ids)[:100]
    
    # Enrich people data
    enriched_people = enricher.enrich_people_data(people_sample, imdb_people)
    
    # Save
    enricher.save_enriched_people(enriched_people, 'data/enriched_people.csv')
    
    print("\n" + "="*50)
    print("PEOPLE ENRICHMENT COMPLETE")
    print("="*50)
    print(f"Total people enriched: {len(enriched_people)}")
    print(f"People with TMDB data: {enriched_people['tmdb_id'].notna().sum()}")
    print(f"People with biography: {enriched_people['biography'].notna().sum()}")
    print("="*50)


if __name__ == "__main__":
    main()
