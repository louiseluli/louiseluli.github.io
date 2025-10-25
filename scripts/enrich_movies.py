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

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("enrich_movies")

def log_resume_summary(df: pd.DataFrame):
    counts = {}
    for col in ("tmdb_done", "omdb_done", "wikidata_done", "ddd_done"):
        if col in df.columns:
            try:
                counts[col] = int(df[col].fillna(False).astype(bool).sum())
            except Exception:
                counts[col] = 0
    if counts:
        logger.info("Resume summary (already done): " + ", ".join(f"{k}={v}" for k, v in counts.items()))

# Dedupe helper ------------------------------------------------
def _squash_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    If identical column names appear (e.g., repeated merges), keep the first,
    combine_first() with subsequent duplicates, and drop the extras.
    """
    name_to_first_idx = {}
    to_drop_idx = []
    for i, name in enumerate(df.columns):
        if name not in name_to_first_idx:
            name_to_first_idx[name] = i
        else:
            j = name_to_first_idx[name]
            df.iloc[:, j] = df.iloc[:, j].combine_first(df.iloc[:, i])
            to_drop_idx.append(i)
    if to_drop_idx:
        df = df.drop(df.columns[to_drop_idx], axis=1)
    return df
# ----------------------------------------------------------------------



# ---------------------------------------------------------------------
# Path resolution helpers
# ---------------------------------------------------------------------
WATCHLIST_CANDIDATES = [
    Path("data/Watched.csv"),
    Path("pages/Watched.csv"),
    Path("/mnt/data/Watched.csv"),
    Path("/mnt/project/Watched.csv"),
]

CHECKPOINT_PATH = Path("data/data/enriched_checkpoint.parquet")

def merge_from_checkpoint(df: pd.DataFrame, id_col: str = "Const") -> pd.DataFrame:
    """If a checkpoint exists, outer-merge it and keep existing non-nulls from checkpoint."""
    if not CHECKPOINT_PATH.exists():
        return df
    try:
        df_ckpt = pd.read_parquet(CHECKPOINT_PATH)
        if id_col in df_ckpt.columns:
            merged = df.merge(df_ckpt.drop_duplicates(id_col), on=id_col, how="left", suffixes=("", "_ckpt"))
            # Prefer latest non-null values from checkpoint
            for col in list(merged.columns):
                if col.endswith("_ckpt"):
                    base = col[:-5]
                    merged[base] = merged[base].combine_first(merged[col])
            drop_cols = [c for c in merged.columns if c.endswith("_ckpt")]
            if drop_cols:
                merged = merged.drop(columns=drop_cols)
            merged = _squash_duplicate_columns(merged)
            logger.info(f"Merged prior checkpoint: {len(df_ckpt)} rows enriched previously.")
            return merged

    except Exception as e:
        logger.warning(f"Could not merge from checkpoint {CHECKPOINT_PATH}: {e}")
    return df



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

    def download_imdb_datasets(self, output_dir: str = "data/data/imdb"):
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

    def enrich_with_imdb(self, df: pd.DataFrame, imdb_dir: str = "data/data/imdb") -> pd.DataFrame:
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
        

        df = _squash_duplicate_columns(df)
        logger.info("IMDb enrichment complete.")
        return df

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

    def _process_with_resume(
        self,
        df: pd.DataFrame,
        provider_name: str,
        per_row_fn,
        done_col: str,
        id_col: str = "Const",
        checkpoint_path: Path = CHECKPOINT_PATH,
        checkpoint_every: int = 50,
    ) -> pd.DataFrame:
        # Load prior checkpoint, merge on id
        if checkpoint_path.exists():
            try:
                df_ckpt = pd.read_parquet(checkpoint_path)
                if id_col in df_ckpt.columns:
                    df = df.merge(df_ckpt.drop_duplicates(id_col), on=id_col, how="left", suffixes=("", "_ckpt"))
                    for col in df.columns:
                        if col.endswith("_ckpt"):
                            base = col[:-5]
                            df[base] = df[base].combine_first(df[col])
                    df = df.drop(columns=[c for c in df.columns if c.endswith("_ckpt")])
            except Exception as e:
                logger.warning(f"Could not load checkpoint {checkpoint_path}: {e}")

        if done_col not in df.columns:
            df[done_col] = False

        total = len(df)
        processed_since_ckpt = 0

        for idx, row in df.iterrows():
            if bool(row.get(done_col, False)):
                continue
            try:
                updates = per_row_fn(row)
            except KeyboardInterrupt:
                logger.info("Interrupted. Writing checkpoint before exiting...")
                checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(checkpoint_path, index=False)
                raise
            except Exception as e:
                logger.warning(f"{provider_name} failed for {row.get(id_col)}: {e}")
                updates = {}

            if updates:
                for k, v in updates.items():
                    if k not in df.columns:
                        df[k] = None
                    df.at[idx, k] = v

            if updates.get("_ok"):
                df.at[idx, done_col] = True

            if idx % 50 == 0:
                logger.info(f"Processing {provider_name} {idx+1}/{total}")

            processed_since_ckpt += 1
            if processed_since_ckpt >= checkpoint_every:
                checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(checkpoint_path, index=False)
                processed_since_ckpt = 0
                time.sleep(self.request_delay)

        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(checkpoint_path, index=False)
        return df



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

        # Make sure expected columns exist
        required_cols = [
            "tmdb_id", "tmdb_tagline", "tmdb_keywords", "tmdb_recommendations",
            "tmdb_similar", "tmdb_images", "genres_merged", "tmdb_overview",
            "tmdb_budget", "tmdb_revenue", "tmdb_runtime",
        ]
        for c in required_cols + ["tmdb_done"]:
            if c not in df.columns:
                df[c] = None
        if "tmdb_done" not in df.columns:
            df["tmdb_done"] = False

        def _per_row(row):
            imdb_id = row.get("Const")
            if not imdb_id or not isinstance(imdb_id, str):
                return {}

            # Skip if we already have a TMDB id and consider it done
            if row.get("tmdb_id"):
                return {"_ok": True}

            tmdb = self.get_tmdb_movie_details(imdb_id)
            if not tmdb:
                # Not fatal — just mark as tried; don’t set _ok so it can retry later
                return {}

            # Extract and merge data
            extracted = self.extract_tmdb_data(tmdb)
            merged_genres = self.merge_genres(row.get("genres"), extracted.get("genres", []))

            return {
                "tmdb_id": extracted.get("tmdb_id"),
                "tmdb_tagline": extracted.get("tagline"),
                "tmdb_keywords": json.dumps(extracted.get("keywords", []), ensure_ascii=False),
                "tmdb_recommendations": json.dumps(extracted.get("recommendations", []), ensure_ascii=False),
                "tmdb_similar": json.dumps(extracted.get("similar", []), ensure_ascii=False),
                "tmdb_images": json.dumps(extracted.get("images", {}), ensure_ascii=False),
                "genres_merged": merged_genres,
                "tmdb_overview": extracted.get("overview"),
                "tmdb_budget": extracted.get("budget"),
                "tmdb_revenue": extracted.get("revenue"),
                "tmdb_runtime": extracted.get("runtime"),
                "_ok": True,
            }

        return self._process_with_resume(
            df=df,
            provider_name="TMDB",
            per_row_fn=_per_row,
            done_col="tmdb_done",
        )


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

        for c in ["omdb_json", "omdb_imdbRating", "omdb_imdbVotes", "omdb_metascore", "omdb_done"]:
            if c not in df.columns:
                df[c] = None
        if "omdb_done" not in df.columns:
            df["omdb_done"] = False

        if not self.omdb_api_key:
            logger.warning("No OMDB API key configured; skipping OMDB.")
            return df

        def _per_row(row):
            imdb_id = row.get("Const")
            if not imdb_id or not isinstance(imdb_id, str):
                return {}

            # If we already have a stored OMDB blob or rating, consider done
            if pd.notna(row.get("omdb_json")) or pd.notna(row.get("omdb_imdbRating")):
                return {"_ok": True}

            try:
                params = {"apikey": self.omdb_api_key, "i": imdb_id, "plot": "full"}
                r = requests.get(self.omdb_base_url, params=params, timeout=20)
                r.raise_for_status()
                data = r.json()
                if data.get("Response") == "False":
                    # Do not mark ok to allow retry later (e.g., once key is fixed)
                    logger.warning(f"OMDB negative response for {imdb_id}: {data.get('Error')}")
                    return {}
                return {
                    "omdb_json": json.dumps(data, ensure_ascii=False),
                    "omdb_imdbRating": data.get("imdbRating"),
                    "omdb_imdbVotes": data.get("imdbVotes"),
                    "omdb_metascore": data.get("Metascore"),
                    "_ok": True,
                }
            except requests.HTTPError as e:
                # Your logs show 401 — most likely an invalid/expired key.
                logger.warning(f"OMDB fetch failed for {imdb_id}: {e}")
                return {}
            finally:
                time.sleep(self.request_delay)

        return self._process_with_resume(
            df=df,
            provider_name="OMDB",
            per_row_fn=_per_row,
            done_col="omdb_done",
        )


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

        for c in ["wikidata_qid", "wikidata_json", "wikidata_done"]:
            if c not in df.columns:
                df[c] = None
        if "wikidata_done" not in df.columns:
            df["wikidata_done"] = False

        def _per_row(row):
            imdb_id = row.get("Const")
            if not imdb_id:
                return {}
            # Already enriched? skip
            if bool(row.get("wikidata_done")) or pd.notna(row.get("wikidata_qid")):
                return {"_ok": True}

            query = f"""
            SELECT ?item WHERE {{
            ?item wdt:P345 "{imdb_id}" .
            }} LIMIT 1
            """

            # simple retry/backoff on timeouts or transient errors
            last_err = None
            for attempt in range(3):
                try:
                    r = requests.get(
                        self.wikidata_endpoint,
                        params={"format": "json", "query": query},
                        headers={"User-Agent": "louise-portfolio/1.0 (resume-enricher)"},
                        timeout=60 if attempt == 2 else 30,  # give extra time on last try
                    )
                    r.raise_for_status()
                    data = r.json()
                    bindings = data.get("results", {}).get("bindings", [])
                    if not bindings:
                        # No QID found—don’t mark as done so you can try again later if desired
                        return {}
                    qid = bindings[0]["item"]["value"].rsplit("/", 1)[-1]
                    return {
                        "wikidata_qid": qid,
                        "wikidata_json": json.dumps(data, ensure_ascii=False),
                        "_ok": True,
                    }
                except Exception as e:
                    last_err = e
                    time.sleep(1.5 * (attempt + 1))
            logger.warning(f"Wikidata fetch failed for {imdb_id}: {last_err}")
            return {}
        return self._process_with_resume(
            df=df,
            provider_name="WIKIDATA",
            per_row_fn=_per_row,
            done_col="wikidata_done",
        )
        
    def enrich_with_ddd(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Enriching with DoesTheDogDie...")

        # ensure columns exist
        for c in ["ddd_json", "ddd_done"]:
            if c not in df.columns:
                df[c] = None
        if "ddd_done" not in df.columns:
            df["ddd_done"] = False

        def _per_row(row):
            title = row.get("Title") or row.get("originalTitle")
            year = row.get("Year") or row.get("startYear")
            if not title:
                return {}
            if bool(row.get("ddd_done")) or pd.notna(row.get("ddd_json")):
                return {"_ok": True}
            try:
                q = f"{title} {year}".strip()
                url = f"{self.dtd_base_url}?q={quote(q)}"
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                text = r.text.strip()
                if not text:
                    return {}  # no data, allow retry later
                return {"ddd_json": text, "_ok": True}
            except Exception as e:
                logger.warning(f"DDD fetch failed for '{title}': {e}")
                return {}
            finally:
                time.sleep(self.request_delay)

        return self._process_with_resume(
            df=df,
            provider_name="DDD",
            per_row_fn=_per_row,
            done_col="ddd_done",
        )
    def save_enriched_data(self, df: pd.DataFrame, out_csv: Path):
        """Write the human CSV and update the resume checkpoint, preserving past enrichment."""
        # 1) Merge with existing checkpoint if present (preserve older non-nulls)
        if CHECKPOINT_PATH.exists():
            try:
                df_prev = pd.read_parquet(CHECKPOINT_PATH)
                if "Const" in df_prev.columns:
                    merged = df.merge(df_prev.drop_duplicates("Const"), on="Const", how="left", suffixes=("", "_old"))
                    # prefer current values, backfill from _old
                    for col in list(merged.columns):
                        if col.endswith("_old"):
                            base = col[:-4]
                            if base not in merged.columns:
                                merged[base] = merged[col]
                            else:
                                merged[base] = merged[base].combine_first(merged[col])
                    merged = merged.drop(columns=[c for c in merged.columns if c.endswith("_old")])
                    df = merged
                    logger.info("Preserved prior enrichment while saving (merged existing checkpoint).")
            except Exception as e:
                logger.warning(f"Could not merge existing checkpoint while saving: {e}")

        # 2) Final guard: remove any truly duplicate column names
        df = _squash_duplicate_columns(df)

        # 3) Write CSV + checkpoint
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(CHECKPOINT_PATH, index=False)
        logger.info(f"Wrote {len(df)} rows to {out_csv} and checkpoint to {CHECKPOINT_PATH}")


        # 2) write CSV + checkpoint
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(CHECKPOINT_PATH, index=False)
        logger.info(f"Wrote {len(df)} rows to {out_csv} and checkpoint to {CHECKPOINT_PATH}")


    



    def create_summary_report(self, df: pd.DataFrame) -> Dict:
        # Coerce possibly-string numeric fields safely
        avg_rating = None
        if "averageRating" in df:
            avg_rating = pd.to_numeric(df["averageRating"], errors="coerce").mean()
            if pd.isna(avg_rating):
                avg_rating = None
            else:
                avg_rating = float(avg_rating)

        total_runtime_hours = None
        if "runtimeMinutes" in df:
            rt_sum = pd.to_numeric(df["runtimeMinutes"], errors="coerce").fillna(0).sum()
            total_runtime_hours = float(rt_sum) / 60.0

        # Year range: prefer explicit Year; fall back to startYear
        year_range = "N/A"
        if "Year" in df:
            y = pd.to_numeric(df["Year"], errors="coerce")
            if not y.dropna().empty:
                year_range = f"{int(y.min())} - {int(y.max())}"
        if year_range == "N/A" and "startYear" in df:
            sy = pd.to_numeric(df["startYear"], errors="coerce")
            if not sy.dropna().empty:
                year_range = f"{int(sy.min())} - {int(sy.max())}"

        return {
            "total_movies": int(len(df)),
            "movies_with_tmdb_data": int(df["tmdb_id"].notna().sum()) if "tmdb_id" in df else 0,
            "movies_with_omdb_data": int(df["omdb_json"].notna().sum()) if "omdb_json" in df else 0,
            "movies_with_wikidata": int(df["wikidata_qid"].notna().sum()) if "wikidata_qid" in df else 0,
            "unique_genres": len(set(g for s in df.get("genres_merged", pd.Series([])).dropna() for g in s.split(", "))),
            "avg_rating": avg_rating,
            "total_runtime_hours": total_runtime_hours,
            "year_range": year_range,
        }


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def parse_args():
    import argparse
    p = argparse.ArgumentParser(description="Enrich movie data from multiple sources.")
    p.add_argument("--watchlist", help="Path to Watched.csv (defaults to auto-discovery).")
    p.add_argument("--sample", type=int, default=-1, help="Rows to enrich (-1 = ALL). Default: -1")
    p.add_argument("--out", default="data/data/enriched_movies.csv", help="Output CSV.")
    p.add_argument("--skip-omdb", action="store_true", help="Skip the OMDB step.")
    p.add_argument("--omdb-only-missing", action="store_true",
                   help="When running OMDB, only query rows still missing OMDB fields.")
    p.add_argument("--providers",
                   type=str,
                   
                   default="imdb,tmdb,omdb,wikidata,ddd",
                   help="Comma-separated list of providers to run (default: all).")
    return p.parse_args()


def main():
    args = parse_args()

    omdb_key = os.getenv("OMDB_API_KEY")
    tmdb_key = os.getenv("TMDB_API_KEY")
    if not tmdb_key:
        logger.warning("TMDB_API_KEY not found in environment; TMDB lookups may fail.")
    if not omdb_key:
        logger.warning("OMDB_API_KEY not found; OMDB step will be skipped unless --skip-omdb is passed.")


    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "YOUR_TMDB_API_KEY")
    OMDB_API_KEY = os.getenv("OMDB_API_KEY", "YOUR_OMDB_API_KEY")

    enricher = MovieDataEnricher(TMDB_API_KEY, OMDB_API_KEY)

    # Resolve & load watchlist
    watchlist_path = resolve_watchlist(args.watchlist)
    providers = [p.strip().lower() for p in args.providers.split(",") if p.strip()]

    # Load (or start) the working dataframe
    df = enricher.load_watchlist(resolve_watchlist(args.watchlist))
    # 🔧 NEW: pull in everything previously enriched so we never “lose” columns/results on save
    df = merge_from_checkpoint(df)
    log_resume_summary(df)


    # Always ensure IMDb cache exists if imdb requested
    if "imdb" in providers:
        enricher.download_imdb_datasets()
        df = enricher.enrich_with_imdb(df)

    # Run selected online providers with resume/checkpoint behavior
    if "tmdb" in providers:
        df = enricher.enrich_with_tmdb(df)

    if "omdb" in providers and not args.skip_omdb:
        df = enricher.enrich_with_omdb(df)

    if "wikidata" in providers:
        df = enricher.enrich_with_wikidata(df)

    if "ddd" in providers:
        df = enricher.enrich_with_ddd(df)

    # Final write
    out_csv = Path("data/data/Watched_enriched.csv")
    enricher.save_enriched_data(df, out_csv)




    # Save & report
    out_path = Path(args.out)
    enricher.save_enriched_data(df, out_path)
    report = enricher.create_summary_report(df)



    print("\n" + "=" * 50)
    print("ENRICHMENT SUMMARY REPORT")
    print("=" * 50)
    for k, v in report.items():
        print(f"{k.replace('_',' ').title()}: {v}")
    print("=" * 50)

if __name__ == "__main__":
    main()
