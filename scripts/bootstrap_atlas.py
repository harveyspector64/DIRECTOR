#!/usr/bin/env python3
import argparse
import json
import math
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

import requests

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

GENRE_MAP = {
    "action film": "action",
    "thriller film": "thriller",
    "crime film": "crime",
    "comedy film": "comedy",
    "horror film": "horror",
    "science fiction film": "scifi",
    "drama film": "drama",
    "romance film": "romance",
    "family film": "family",
    "animated film": "animation",
    "animation": "animation",
}

LANES = [
    "action",
    "thriller",
    "crime",
    "comedy",
    "horror",
    "scifi",
    "drama",
    "romance",
    "family",
    "animation",
]


def run_query(query: str) -> dict:
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "DirectorRadarBot/0.1 (https://example.com)"
    }
    response = requests.get(SPARQL_ENDPOINT, params={"query": query}, headers=headers, timeout=60)
    response.raise_for_status()
    return response.json()


def normalize_genres(genres: List[str]) -> List[str]:
    normalized = set()
    for genre in genres:
        key = genre.lower()
        if key in GENRE_MAP:
            normalized.add(GENRE_MAP[key])
    return sorted(normalized)


def compute_lane_fingerprint(recent_features: List[dict]) -> Dict[str, float]:
    weights = {lane: 0.0 for lane in LANES}
    if not recent_features:
        return weights
    total = 0.0
    for feature in recent_features:
        for genre in feature.get("genres_normalized", []):
            weights[genre] += 1.0
            total += 1.0
    if total == 0:
        return weights
    return {lane: round(value / total, 2) for lane, value in weights.items()}


def compute_assignment_score(films: List[dict]) -> float:
    if not films:
        return 0.0
    total = len(films)
    with_writer = sum(1 for film in films if film.get("director_is_writer"))
    return round(with_writer / total, 2)


def compute_scale_proxy(film_count: int) -> str:
    if film_count >= 6:
        return "large"
    if film_count >= 3:
        return "mid"
    return "small"


def compute_adjacency(edges: List[dict]) -> List[dict]:
    weighted = defaultdict(float)
    last_year = {}
    for edge in edges:
        weighted[edge["actor_id"]] += edge["weight"]
        last_year[edge["actor_id"]] = max(last_year.get(edge["actor_id"], 0), edge.get("year", 0))
    top = sorted(weighted.items(), key=lambda item: item[1], reverse=True)[:10]
    return [
        {
            "actor_id": actor_id,
            "actor_name": edge_lookup.get(actor_id, "Unknown"),
            "weight": round(weight, 2),
            "last_worked_year": last_year.get(actor_id)
        }
        for actor_id, weight in top
    ]


edge_lookup: Dict[str, str] = {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min_year", type=int, default=2008)
    parser.add_argument("--target", type=int, default=3000)
    parser.add_argument("--page_size", type=int, default=500)
    args = parser.parse_args()

    directors: Dict[str, dict] = {}
    films: Dict[str, dict] = {}
    actors: Dict[str, dict] = {}
    edges: List[dict] = []

    pages = math.ceil(args.target / args.page_size)
    for page in range(pages):
        offset = page * args.page_size
        query = f"""
        SELECT ?film ?filmLabel ?director ?directorLabel ?year ?genreLabel ?cast ?castLabel ?writer
        WHERE {{
          ?film wdt:P31/wdt:P279* wd:Q11424;  # film
                wdt:P57 ?director;
                wdt:P577 ?date.
          BIND(YEAR(?date) AS ?year)
          FILTER(?year >= {args.min_year})
          OPTIONAL {{ ?film wdt:P136 ?genre. ?genre rdfs:label ?genreLabel FILTER(LANG(?genreLabel) = 'en') }}
          OPTIONAL {{ ?film wdt:P161 ?cast. ?cast rdfs:label ?castLabel FILTER(LANG(?castLabel) = 'en') }}
          OPTIONAL {{ ?film wdt:P58 ?writer. }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT {args.page_size}
        OFFSET {offset}
        """
        data = run_query(query)
        results = data.get("results", {}).get("bindings", [])
        if not results:
            break
        for row in results:
            film_id = row["film"]["value"].split("/")[-1]
            director_id = row["director"]["value"].split("/")[-1]
            actor_id = row.get("cast", {}).get("value")
            actor_label = row.get("castLabel", {}).get("value")
            if actor_id:
                actor_id = actor_id.split("/")[-1]
                edge_lookup[actor_id] = actor_label
            director = directors.setdefault(
                director_id,
                {
                    "id": director_id,
                    "name": row["directorLabel"]["value"],
                    "aliases": [],
                    "countries": [],
                    "recent_features": [],
                    "lane_fingerprint": {lane: 0.0 for lane in LANES},
                    "assignment_score": 0.0,
                    "scale_proxy": "small",
                    "cast_adjacency_top": [],
                    "availability": {
                        "status": "UNKNOWN",
                        "next_likely_open_window": None,
                        "confidence": "low",
                        "last_verified": datetime.utcnow().date().isoformat(),
                    },
                    "current_events": [],
                    "data_freshness": {
                        "last_event_seen": None,
                        "last_profile_rebuild": datetime.utcnow().date().isoformat(),
                    },
                },
            )
            film = films.setdefault(
                film_id,
                {
                    "id": film_id,
                    "title": row["filmLabel"]["value"],
                    "year": int(row["year"]["value"]),
                    "director_id": director_id,
                    "genres": set(),
                    "cast": set(),
                    "director_is_writer": False,
                },
            )
            if row.get("genreLabel"):
                film["genres"].add(row["genreLabel"]["value"])
            if actor_id:
                film["cast"].add(actor_id)
            if row.get("writer"):
                writer_id = row["writer"]["value"].split("/")[-1]
                if writer_id == director_id:
                    film["director_is_writer"] = True

        time.sleep(1)

    for film in films.values():
        director = directors.get(film["director_id"])
        if not director:
            continue
        genres_normalized = normalize_genres(list(film["genres"]))
        director["recent_features"].append(
            {
                "title": film["title"],
                "year": film["year"],
                "film_id": film["id"],
                "genres_normalized": genres_normalized,
                "top_cast": list(film["cast"])[:5],
            }
        )
        for actor_id in list(film["cast"])[:5]:
            edges.append(
                {
                    "director_id": film["director_id"],
                    "actor_id": actor_id,
                    "film_id": film["id"],
                    "year": film["year"],
                    "weight": 1.0,
                }
            )
            actors.setdefault(
                actor_id,
                {
                    "id": actor_id,
                    "name": edge_lookup.get(actor_id, "Unknown"),
                    "recent_director_edges": [],
                    "adjacency_top": [],
                },
            )

    for director in directors.values():
        director["recent_features"] = sorted(
            director["recent_features"], key=lambda item: item["year"], reverse=True
        )[:5]
        director["last_feature_directed_year"] = director["recent_features"][0]["year"] if director["recent_features"] else None
        director["last_feature_released_year"] = director["last_feature_directed_year"]
        director["lane_fingerprint"] = compute_lane_fingerprint(director["recent_features"])
        film_count = len(director["recent_features"])
        director["assignment_score"] = compute_assignment_score(
            [film for film in films.values() if film["director_id"] == director["id"]]
        )
        director["scale_proxy"] = compute_scale_proxy(film_count)

    for actor in actors.values():
        for edge in edges:
            if edge["actor_id"] != actor["id"]:
                continue
            director = directors.get(edge["director_id"])
            film = films.get(edge["film_id"])
            if not director or not film:
                continue
            actor["recent_director_edges"].append(
                {
                    "director_id": director["id"],
                    "director_name": director["name"],
                    "film_title": film["title"],
                    "year": film["year"],
                }
            )
        adjacency = defaultdict(float)
        for edge in edges:
            if edge["actor_id"] == actor["id"]:
                adjacency[edge["director_id"]] += 1.0
        actor["adjacency_top"] = [
            {"director_id": director_id, "weight": round(weight, 2)}
            for director_id, weight in sorted(adjacency.items(), key=lambda item: item[1], reverse=True)[:10]
        ]

    for director in directors.values():
        director_edges = [edge for edge in edges if edge["director_id"] == director["id"]]
        director["cast_adjacency_top"] = compute_adjacency(director_edges)

    output_directors = list(directors.values())[: args.target]
    output_actors = list(actors.values())
    output_films = [
        {
            "id": film["id"],
            "title": film["title"],
            "year": film["year"],
            "director_id": film["director_id"],
        }
        for film in films.values()
    ]

    with open("data/baseline/directors.json", "w", encoding="utf-8") as handle:
        json.dump(output_directors, handle, indent=2, ensure_ascii=False)
    with open("data/baseline/actors.json", "w", encoding="utf-8") as handle:
        json.dump(output_actors, handle, indent=2, ensure_ascii=False)
    with open("data/baseline/films.json", "w", encoding="utf-8") as handle:
        json.dump(output_films, handle, indent=2, ensure_ascii=False)
    with open("data/baseline/edges.json", "w", encoding="utf-8") as handle:
        json.dump(edges, handle, indent=2, ensure_ascii=False)

    print(f"Wrote {len(output_directors)} directors, {len(output_films)} films, {len(output_actors)} actors")


if __name__ == "__main__":
    main()
