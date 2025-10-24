#!/usr/bin/env python3
"""
People Data Enrichment System
Enriches data for actors, actresses, and directors from:
- IMDb Non-Commercial Datasets
- TMDB (The Movie Database)
- Wikidata
"""

import argparse
import gzip
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("enrich_people")

WATCHLIST_CANDIDATES = [
    Path("data/Watched.csv"),
    Path("pages/Watched.csv"),
    Path("/mnt/data/Watched.csv"),
    Path("/mnt/project/Watched.csv"),
]

def resolve_watchlist(cli_arg: Optional[str]) -> Path:
    if cli_arg:
        p = Path(cli_arg).expanduser().resolve()
        if p.exists():
            return p
        raise FileNotFoundError(f"Watchlist not found at: {p}")
    for p in WATCHLIST_CANDIDATES:
        if p.exists():
            return p.resolve()
    tried = "\n  - " + "\n  - ".join(str(p) for p in WATCHLIST_CANDIDATES)
    raise FileNotFoundError(
        "Could not find Watched.csv. I looked in:" + tried +
        "\nTip: pass --watchlist PATH or move the file to data/Watched.csv"
    )

class PeopleDataEnricher:
    def __init__(self, tmdb_api_key: str):
        self.tmdb_api_key = tmdb_api_key
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.wikidata_endpoint = "https://query.wikidata.org/sparql"
        self.request_delay = 0.25

    def load_imdb_people(self, filepath: str = "data/imdb/name.basics.tsv.gz") -> pd.DataFrame:
        logger.info("Loading IMDb names dataset...")
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            df = pd.read_csv(f, sep="\t", na_values="\\N", low_memory=False)
        logger.info(f"Loaded {len(df)} people from IMDb")
        return df

    def extract_people_from_movies(self, movies_df: pd.DataFrame,
                                   principals_path: str = "data/imdb/title.principals.tsv.gz") -> List[str]:
        logger.info("Extracting people from watched movies...")
        with gzip.open(principals_path, "rt", encoding="utf-8") as f:
            principals = pd.read_csv(f, sep="\t", na_values="\\N", low_memory=False)
        movie_ids = set(movies_df["Const"].values)
        people_in_movies = principals[principals["tconst"].isin(movie_ids)]
        unique_people = people_in_movies["nconst"].dropna().unique().tolist()
        logger.info(f"Found {len(unique_people)} unique people in watched movies")
        return unique_people

    def get_tmdb_person_details(self, imdb_id: str) -> Optional[Dict]:
        try:
            url = f"{self.tmdb_base_url}/find/{imdb_id}"
            params = {"api_key": self.tmdb_api_key, "external_source": "imdb_id"}
            r = requests.get(url, params=params); r.raise_for_status()
            data = r.json()
            if not data.get("person_results"):
                return None

            person_id = data["person_results"][0]["id"]
            url = f"{self.tmdb_base_url}/person/{person_id}"
            params = {"api_key": self.tmdb_api_key, "append_to_response": "combined_credits,images"}
            time.sleep(self.request_delay)
            r = requests.get(url, params=params); r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning(f"TMDB person fetch failed for {imdb_id}: {e}")
            return None

    def extract_tmdb_person_data(self, tmdb_data: Dict) -> Dict:
        if not tmdb_data:
            return {}
        gender_map = {0: "Not set", 1: "Female", 2: "Male", 3: "Non-binary"}

        images = []
        if tmdb_data.get("images", {}).get("profiles"):
            images = [img["file_path"] for img in tmdb_data["images"]["profiles"][:5]]

        combined_credits = {"cast": [], "crew": []}
        if tmdb_data.get("combined_credits"):
            if tmdb_data["combined_credits"].get("cast"):
                combined_credits["cast"] = [
                    {"title": c.get("title") or c.get("name"), "character": c.get("character"), "id": c.get("id")}
                    for c in tmdb_data["combined_credits"]["cast"][:20]
                ]
            if tmdb_data["combined_credits"].get("crew"):
                combined_credits["crew"] = [
                    {"title": c.get("title") or c.get("name"), "job": c.get("job"),
                     "department": c.get("department"), "id": c.get("id")}
                    for c in tmdb_data["combined_credits"]["crew"][:20]
                ]

        return {
            "tmdb_id": tmdb_data.get("id"),
            "imdb_id": tmdb_data.get("imdb_id"),
            "gender": gender_map.get(tmdb_data.get("gender", 0), "Not set"),
            "also_known_as": tmdb_data.get("also_known_as", []),
            "biography": tmdb_data.get("biography"),
            "birthday": tmdb_data.get("birthday"),
            "deathday": tmdb_data.get("deathday"),
            "place_of_birth": tmdb_data.get("place_of_birth"),
            "profile_images": images,
            "combined_credits": combined_credits,
            "known_for_department": tmdb_data.get("known_for_department"),
            "popularity": tmdb_data.get("popularity"),
        }

    def query_wikidata_person(self, imdb_id: str) -> Optional[Dict]:
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
            r = requests.get(self.wikidata_endpoint,
                             params={"query": query, "format": "json"},
                             headers={"User-Agent": "PeopleEnricher/1.0"})
            r.raise_for_status()
            data = r.json()
            if data["results"]["bindings"]:
                return data["results"]["bindings"][0]
            return None
        except Exception as e:
            logger.warning(f"Wikidata person query failed for {imdb_id}: {e}")
            return None

    def enrich_people_data(self, people_ids: List[str], imdb_people: pd.DataFrame) -> pd.DataFrame:
        logger.info(f"Enriching data for {len(people_ids)} people...")
        enriched = []

        for idx, person_id in enumerate(people_ids):
            if idx % 50 == 0:
                logger.info(f"Processing person {idx + 1}/{len(people_ids)}")

            # IMDb base
            imdb_row = imdb_people[imdb_people["nconst"] == person_id]
            if imdb_row.empty:
                continue
            r0 = imdb_row.iloc[0]
            person_info = {
                "nconst": person_id,
                "imdb_name": r0.get("primaryName"),
                "birth_year_imdb": r0.get("birthYear"),
                "death_year_imdb": r0.get("deathYear"),
                "primary_profession": r0.get("primaryProfession"),
                "known_for_titles": r0.get("knownForTitles"),
            }

            # TMDB
            tmdb_data = self.get_tmdb_person_details(person_id)
            if tmdb_data:
                ex = self.extract_tmdb_person_data(tmdb_data)
                person_info.update({
                    "tmdb_id": ex.get("tmdb_id"),
                    "gender": ex.get("gender"),
                    "also_known_as": json.dumps(ex.get("also_known_as", [])),
                    "biography": ex.get("biography"),
                    "birthday": ex.get("birthday"),
                    "deathday": ex.get("deathday"),
                    "place_of_birth": ex.get("place_of_birth"),
                    "profile_images": json.dumps(ex.get("profile_images", [])),
                    "combined_credits": json.dumps(ex.get("combined_credits", {})),
                    "known_for_department": ex.get("known_for_department"),
                    "popularity": ex.get("popularity"),
                })

            # Wikidata
            wd = self.query_wikidata_person(person_id)
            if wd:
                person_info.update({
                    "wiki_nickname": wd.get("nickname", {}).get("value"),
                    "wiki_pseudonym": wd.get("pseudonym", {}).get("value"),
                    "wiki_family_name": wd.get("familyName", {}).get("value"),
                    "wiki_given_name": wd.get("givenName", {}).get("value"),
                    "wiki_birth_name": wd.get("birthName", {}).get("value"),
                    "wiki_ethnic_group": wd.get("ethnicGroup", {}).get("value"),
                    "wiki_height": wd.get("height", {}).get("value"),
                    "wiki_eye_color": wd.get("eyeColor", {}).get("value"),
                    "wiki_hair_color": wd.get("hairColor", {}).get("value"),
                })

            enriched.append(person_info)
            time.sleep(0.3)

        df = pd.DataFrame(enriched)
        logger.info(f"Enriched {len(df)} people")
        return df

def parse_args():
    p = argparse.ArgumentParser(description="Enrich people (actors, directors) from watchlist.")
    p.add_argument("--watchlist", help="Path to Watched.csv (defaults to auto-discovery).")
    p.add_argument("--sample", type=int, default=-1,
                   help="Number of people to enrich (use -1 for ALL). Default: -1")
    p.add_argument("--out", default="data/enriched_people.csv",
                   help="Output CSV (default: data/enriched_people.csv)")
    return p.parse_args()

def main():
    args = parse_args()

    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "YOUR_TMDB_API_KEY")
    enricher = PeopleDataEnricher(TMDB_API_KEY)

    # IMDb names
    imdb_people = enricher.load_imdb_people()

    # Watchlist (robust path)
    watchlist_path = resolve_watchlist(args.watchlist)
    movies_df = pd.read_csv(watchlist_path, encoding="utf-8-sig")

    # Extract nconsts from principals for titles in watchlist
    people_ids = enricher.extract_people_from_movies(movies_df)
    if args.sample is not None and args.sample > -1:
        people_ids = people_ids[: args.sample]


    # Enrich & save
    enriched_people = enricher.enrich_people_data(people_ids, imdb_people)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    enriched_people.to_csv(out_path, index=False)

    print("\n" + "=" * 50)
    print("PEOPLE ENRICHMENT COMPLETE")
    print("=" * 50)
    print(f"Total people enriched: {len(enriched_people)}")
    if "tmdb_id" in enriched_people:
        print(f"People with TMDB data: {enriched_people['tmdb_id'].notna().sum()}")
    if "biography" in enriched_people:
        print(f"People with biography: {enriched_people['biography'].notna().sum()}")
    print("=" * 50)

if __name__ == "__main__":
    main()
