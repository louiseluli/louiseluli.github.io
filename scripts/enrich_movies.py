#!/usr/bin/env python3
"""
Movie Data Enrichment System
Enriches movie data from IMDb watchlist with:
- IMDb Non-Commercial Datasets
- TMDB (The Movie Database)
- OMDB (Open Movie Database)
- Wikidata
- DoesTheDogDie API
"""

import argparse
import gzip
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

import pandas as pd
import requests

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("enrich_movies")

# ---------------------------------------------------------------------
# Path resolution helpers
# ---------------------------------------------------------------------
WATCHLIST_CANDIDATES = [
    Path("data/Watched.csv"),
    Path("pages/Watched.csv"),
    Path("/mnt/data/Watched.csv"),
    Path("/mnt/project/Watched.csv"),
]

def resolve_watchlist(cli_arg: Optional[str]) -> Path:
    """Return a valid path to Watched.csv, trying common locations."""
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

def ensure_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# Enricher
# ---------------------------------------------------------------------
class MovieDataEnricher:
    """Main class for enriching movie data from multiple sources"""

    def __init__(self, tmdb_api_key: str, omdb_api_key: str):
        self.tmdb_api_key = tmdb_api_key
        self.omdb_api_key = omdb_api_key
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.omdb_base_url = "http://www.omdbapi.com/"
        self.wikidata_endpoint = "https://query.wikidata.org/sparql"
        self.dtd_base_url = "https://www.doesthedogdie.com/dddsearch"
        self.request_delay = 0.25  # 4 rps

    def load_watchlist(self, filepath: Path) -> pd.DataFrame:
        logger.info(f"Loading watchlist from {filepath}")
        df = pd.read_csv(filepath, encoding="utf-8-sig")
        logger.info(f"Loaded {len(df)} movies")
        return df

    def download_imdb_datasets(self, output_dir: str = "data/imdb"):
        logger.info("Ensuring IMDb datasets exist...")
        os.makedirs(output_dir, exist_ok=True)

        datasets = [
            "title.basics.tsv.gz",
            "title.ratings.tsv.gz",
            "title.crew.tsv.gz",
            "title.principals.tsv.gz",
            "name.basics.tsv.gz",
        ]
        base_url = "https://datasets.imdbws.com/"

        for dataset in datasets:
            url = base_url + dataset
            filepath = os.path.join(output_dir, dataset)
            if os.path.exists(filepath):
                logger.info(f"{dataset} already exists, skipping")
                continue
            logger.info(f"Downloading {dataset} ...")
            try:
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(filepath, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                logger.info(f"Downloaded {dataset}")
            except Exception as e:
                logger.error(f"Error downloading {dataset}: {e}")

    def load_imdb_dataset(self, filepath: str) -> pd.DataFrame:
        logger.info(f"Loading IMDb dataset: {filepath}")
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            df = pd.read_csv(f, sep="\t", na_values="\\N", low_memory=False)
        logger.info(f"Loaded {len(df)} rows from {Path(filepath).name}")
        return df

    def enrich_with_imdb(self, df: pd.DataFrame, imdb_dir: str = "data/imdb") -> pd.DataFrame:
        logger.info("Enriching with IMDb data...")
        basics = self.load_imdb_dataset(os.path.join(imdb_dir, "title.basics.tsv.gz"))
        ratings = self.load_imdb_dataset(os.path.join(imdb_dir, "title.ratings.tsv.gz"))
        crew = self.load_imdb_dataset(os.path.join(imdb_dir, "title.crew.tsv.gz"))

        # Join basics
        df = df.merge(
            basics[["tconst", "originalTitle", "startYear", "runtimeMinutes", "genres"]],
            left_on="Const",
            right_on="tconst",
            how="left",
            suffixes=("", "_imdb"),
        )

        # Ratings
        df = df.merge(
            ratings[["tconst", "averageRating", "numVotes"]],
            on="tconst",
            how="left",
            suffixes=("", "_imdbd"),
        )

        # Crew
        df = df.merge(
            crew[["tconst", "directors", "writers"]],
            on="tconst",
            how="left",
            suffixes=("", "_crew"),
        )
        logger.info("IMDb enrichment complete.")
        return df

    def get_tmdb_movie_details(self, imdb_id: str) -> Optional[Dict]:
        try:
            url = f"{self.tmdb_base_url}/find/{imdb_id}"
            params = {"api_key": self.tmdb_api_key, "external_source": "imdb_id"}
            r = requests.get(url, params=params); r.raise_for_status()
            data = r.json()
            if not data.get("movie_results"):
                return None

            movie_id = data["movie_results"][0]["id"]
            url = f"{self.tmdb_base_url}/movie/{movie_id}"
            params = {
                "api_key": self.tmdb_api_key,
                "append_to_response": "keywords,recommendations,similar,images,credits",
            }
            time.sleep(self.request_delay)
            r = requests.get(url, params=params); r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning(f"TMDB fetch failed for {imdb_id}: {e}")
            return None

    def merge_genres(self, imdb_genres: Optional[str], tmdb_genres: List[Dict]) -> str:
        genres = set()
        if pd.notna(imdb_genres):
            for g in str(imdb_genres).split(","):
                g = g.strip()
                genres.add("Science Fiction" if g.lower() in ("sci-fi", "science fiction") else g)
        if tmdb_genres:
            for g in tmdb_genres:
                name = g.get("name", "")
                genres.add("Science Fiction" if name.lower() in ("sci-fi", "science fiction") else name)
        return ", ".join(sorted(x for x in genres if x))

    def extract_tmdb_data(self, tmdb_data: Dict) -> Dict:
        if not tmdb_data:
            return {}
        # Keywords
        keywords = []
        if tmdb_data.get("keywords", {}).get("keywords"):
            keywords = [kw["name"] for kw in tmdb_data["keywords"]["keywords"]]

        # Recs
        recommendations = []
        if tmdb_data.get("recommendations", {}).get("results"):
            recommendations = [{"id": r["id"], "title": r.get("title")} for r in tmdb_data["recommendations"]["results"][:10]]

        # Similar
        similar = []
        if tmdb_data.get("similar", {}).get("results"):
            similar = [{"id": r["id"], "title": r.get("title")} for r in tmdb_data["similar"]["results"][:10]]

        # Images
        images = {"backdrops": [], "posters": [], "logos": []}
        if tmdb_data.get("images"):
            for k in images.keys():
                if tmdb_data["images"].get(k):
                    images[k] = [img["file_path"] for img in tmdb_data["images"][k][:5]]

        return {
            "tmdb_id": tmdb_data.get("id"),
            "imdb_id": tmdb_data.get("imdb_id"),
            "tagline": tmdb_data.get("tagline"),
            "genres": tmdb_data.get("genres", []),
            "keywords": keywords,
            "recommendations": recommendations,
            "similar": similar,
            "images": images,
            "overview": tmdb_data.get("overview"),
            "budget": tmdb_data.get("budget"),
            "revenue": tmdb_data.get("revenue"),
            "runtime": tmdb_data.get("runtime"),
        }

    def enrich_with_tmdb(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Enriching with TMDB...")
        for col in ["tmdb_id", "tmdb_tagline", "tmdb_keywords", "tmdb_recommendations",
                    "tmdb_similar", "tmdb_images", "genres_merged"]:
            if col not in df.columns:
                df[col] = None

        for idx, row in df.iterrows():
            if idx % 50 == 0:
                logger.info(f"Processing TMDB {idx + 1}/{len(df)}")
            imdb_id = row["Const"]
            tmdb_data = self.get_tmdb_movie_details(imdb_id)
            if not tmdb_data:
                continue
            ex = self.extract_tmdb_data(tmdb_data)
            df.at[idx, "tmdb_id"] = ex.get("tmdb_id")
            df.at[idx, "tmdb_tagline"] = ex.get("tagline")
            df.at[idx, "tmdb_keywords"] = json.dumps(ex.get("keywords", []))
            df.at[idx, "tmdb_recommendations"] = json.dumps(ex.get("recommendations", []))
            df.at[idx, "tmdb_similar"] = json.dumps(ex.get("similar", []))
            df.at[idx, "tmdb_images"] = json.dumps(ex.get("images", {}))
            df.at[idx, "genres_merged"] = self.merge_genres(row.get("Genres", row.get("genres")), ex.get("genres", []))
        logger.info("TMDB enrichment complete.")
        return df

    def get_omdb_data(self, imdb_id: str) -> Optional[Dict]:
        try:
            params = {"apikey": self.omdb_api_key, "i": imdb_id, "plot": "full"}
            r = requests.get(self.omdb_base_url, params=params); r.raise_for_status()
            data = r.json()
            if data.get("Response") == "True":
                return {"poster": data.get("Poster"), "plot": data.get("Plot")}
            return None
        except Exception as e:
            logger.warning(f"OMDB fetch failed for {imdb_id}: {e}")
            return None

    def enrich_with_omdb(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Enriching with OMDB...")
        for col in ["omdb_poster", "omdb_plot"]:
            if col not in df.columns:
                df[col] = None

        for idx, row in df.iterrows():
            if idx % 50 == 0:
                logger.info(f"Processing OMDB {idx + 1}/{len(df)}")
            imdb_id = row["Const"]
            om = self.get_omdb_data(imdb_id)
            if om:
                df.at[idx, "omdb_poster"] = om.get("poster")
                df.at[idx, "omdb_plot"] = om.get("plot")
            time.sleep(0.1)
        logger.info("OMDB enrichment complete.")
        return df

    def query_wikidata(self, imdb_id: str) -> Optional[Dict]:
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
            r = requests.get(self.wikidata_endpoint,
                             params={"query": query, "format": "json"},
                             headers={"User-Agent": "MovieEnricher/1.0"})
            r.raise_for_status()
            data = r.json()
            if data["results"]["bindings"]:
                return data["results"]["bindings"][0]
            return None
        except Exception as e:
            logger.warning(f"Wikidata query failed for {imdb_id}: {e}")
            return None

    def enrich_with_wikidata(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Enriching with Wikidata...")
        for col in ["wiki_logo_image", "wiki_main_subject", "wiki_film_poster",
                    "wiki_based_on", "wiki_set_in_period", "wiki_inspired_by"]:
            if col not in df.columns:
                df[col] = None

        for idx, row in df.iterrows():
            if idx % 50 == 0:
                logger.info(f"Processing Wikidata {idx + 1}/{len(df)}")
            imdb_id = row["Const"]
            wd = self.query_wikidata(imdb_id)
            if wd:
                df.at[idx, "wiki_logo_image"] = wd.get("logoImage", {}).get("value")
                df.at[idx, "wiki_main_subject"] = wd.get("mainSubjectLabel", {}).get("value")
                df.at[idx, "wiki_film_poster"] = wd.get("filmPoster", {}).get("value")
                df.at[idx, "wiki_based_on"] = wd.get("basedOnLabel", {}).get("value")
                df.at[idx, "wiki_set_in_period"] = wd.get("setPeriod", {}).get("value")
                df.at[idx, "wiki_inspired_by"] = wd.get("inspiredByLabel", {}).get("value")
            time.sleep(0.5)
        logger.info("Wikidata enrichment complete.")
        return df

    def save_enriched_data(self, df: pd.DataFrame, output_path: Path):
        ensure_dir(Path(output_path))
        logger.info(f"Saving enriched data to {output_path}")
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} rows")

    def create_summary_report(self, df: pd.DataFrame) -> Dict:
        return {
            "total_movies": int(len(df)),
            "movies_with_tmdb_data": int(df["tmdb_id"].notna().sum()) if "tmdb_id" in df else 0,
            "movies_with_omdb_data": int(df["omdb_poster"].notna().sum()) if "omdb_poster" in df else 0,
            "movies_with_wikidata": int(df["wiki_film_poster"].notna().sum()) if "wiki_film_poster" in df else 0,
            "unique_genres": len(set(g for s in df.get("genres_merged", pd.Series([])).dropna() for g in s.split(", "))),
            "avg_rating": float(df.get("IMDb Rating", pd.Series(dtype=float)).mean()) if "IMDb Rating" in df else None,
            "total_runtime_hours": float(df.get("Runtime (mins)", pd.Series(dtype=float)).sum() / 60) if "Runtime (mins)" in df else None,
            "year_range": (
                f"{int(df['Year'].min())} - {int(df['Year'].max())}"
                if "Year" in df and not df["Year"].isna().all()
                else "N/A"
            ),
        }

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="Enrich movie data from multiple sources.")
    p.add_argument("--watchlist", help="Path to Watched.csv (defaults to auto-discovery).")
    p.add_argument("--sample", type=int, default=-1,
                   help="Number of rows to enrich (use -1 for ALL). Default: -1")
    p.add_argument("--out", default="data/enriched_movies.csv",
                   help="Output CSV (default: data/enriched_movies.csv)")
    return p.parse_args()

def main():
    args = parse_args()

    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "YOUR_TMDB_API_KEY")
    OMDB_API_KEY = os.getenv("OMDB_API_KEY", "YOUR_OMDB_API_KEY")

    enricher = MovieDataEnricher(TMDB_API_KEY, OMDB_API_KEY)

    # Resolve & load watchlist
    watchlist_path = resolve_watchlist(args.watchlist)
    df = enricher.load_watchlist(watchlist_path)

    # Ensure IMDb datasets (download if missing)
    enricher.download_imdb_datasets()

    # IMDb enrichment
    df = enricher.enrich_with_imdb(df)

    # API enrichments
    df_enrich = df.copy() if args.sample is None or args.sample < 0 else df.head(args.sample).copy()
    df_enrich = enricher.enrich_with_tmdb(df_enrich)
    df_enrich = enricher.enrich_with_omdb(df_enrich)
    df_enrich = enricher.enrich_with_wikidata(df_enrich)


    # Save & report
    out_path = Path(args.out)
    enricher.save_enriched_data(df_enrich, out_path)
    report = enricher.create_summary_report(df_enrich)


    print("\n" + "=" * 50)
    print("ENRICHMENT SUMMARY REPORT")
    print("=" * 50)
    for k, v in report.items():
        print(f"{k.replace('_',' ').title()}: {v}")
    print("=" * 50)

if __name__ == "__main__":
    main()
