#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import os
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

GENRE_MAP = {
    "action film": "Action",
    "thriller film": "Thriller",
    "crime film": "Crime",
    "comedy film": "Comedy",
    "horror film": "Horror",
    "science fiction film": "Sci-Fi",
    "drama film": "Drama",
    "romance film": "Romance",
    "family film": "Family/YA",
    "children's film": "Family/YA",
    "animated film": "Animation",
    "animation": "Animation",
}

LANES = [
    "Action",
    "Comedy",
    "Thriller",
    "Crime",
    "Horror",
    "Drama",
    "Sci-Fi",
    "Romance",
    "Family/YA",
    "Animation",
    "Other",
]


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def hash_query(query: str) -> str:
    return hashlib.sha1(query.encode("utf-8")).hexdigest()


def fetch_sparql(query: str, cache_dir: str, sleep_s: float = 1.0) -> dict:
    ensure_dir(cache_dir)
    cache_path = os.path.join(cache_dir, f"{hash_query(query)}.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "DirectorRadarBot/0.2 (https://example.com)",
    }
    params = urllib.parse.urlencode({"query": query})
    url = f"{SPARQL_ENDPOINT}?{params}"
    backoff = 2
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for attempt in range(6):
        request = urllib.request.Request(url, headers=headers)
        try:
            with opener.open(request, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
                with open(cache_path, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle)
                time.sleep(sleep_s)
                return payload
        except Exception:
            time.sleep(backoff)
            backoff *= 2
            continue

    raise RuntimeError("Failed to fetch SPARQL after retries")


def normalize_genres(genres: List[str]) -> List[str]:
    normalized = set()
    for genre in genres:
        key = genre.lower()
        if key in GENRE_MAP:
            normalized.add(GENRE_MAP[key])
        else:
            normalized.add("Other")
    return sorted(normalized)


def compute_lane_fingerprint(recent_features: List[dict]) -> Dict[str, float]:
    weights = {lane: 0.0 for lane in LANES}
    features = recent_features[:5]
    if not features:
        return weights
    total = 0.0
    for feature in features:
        for genre in feature.get("genres_normalized", []):
            weights[genre] += 1.0
            total += 1.0
    if total == 0:
        return weights
    return {lane: round(value / total, 3) for lane, value in weights.items()}


def compute_assignment_score(films: List[dict], director_id: str) -> float:
    if not films:
        return 0.0
    total = len(films)
    with_writer = sum(1 for film in films if director_id in film.get("screenwriters", []))
    return round(with_writer / total, 3)


def recency_weight(year: int, current_year: int) -> float:
    age = max(0, current_year - year)
    return max(0.2, 1 / (1 + age / 4))


def billing_weight(order: Optional[int]) -> float:
    if order is None:
        return 1.0
    if order <= 2:
        return 1.4
    if order <= 4:
        return 1.2
    if order <= 8:
        return 1.0
    return 0.8


def compute_cast_adjacency(edges: List[dict], actors_lookup: Dict[str, str]) -> List[dict]:
    weighted = defaultdict(float)
    last_year = {}
    for edge in edges:
        weighted[edge["actor_id"]] += edge["weight"]
        last_year[edge["actor_id"]] = max(last_year.get(edge["actor_id"], 0), edge.get("year", 0))
    top = sorted(weighted.items(), key=lambda item: item[1], reverse=True)[:10]
    return [
        {
            "actor_id": actor_id,
            "actor_name": actors_lookup.get(actor_id, "Unknown"),
            "weight": round(weight, 3),
            "last_worked_year": last_year.get(actor_id),
        }
        for actor_id, weight in top
    ]


def load_checkpoint(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_checkpoint(path: str, payload: dict) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def build_query(min_year: int, limit: int, offset: int) -> str:
    return f"""
    SELECT ?film ?filmLabel ?director ?directorLabel ?year ?genreLabel ?cast ?castLabel ?castOrder ?directorSitelinks ?directorStatements ?screenwriter
    WHERE {{
      ?film wdt:P31/wdt:P279* wd:Q11424;
            wdt:P57 ?director;
            wdt:P577 ?date.
      BIND(YEAR(?date) AS ?year)
      FILTER(?year >= {min_year})

      OPTIONAL {{ ?film wdt:P136 ?genre. ?genre rdfs:label ?genreLabel FILTER(LANG(?genreLabel) = 'en') }}
      OPTIONAL {{
        ?film p:P161 ?castStmt.
        ?castStmt ps:P161 ?cast.
        OPTIONAL {{ ?castStmt pq:P1545 ?castOrder }}
        ?cast rdfs:label ?castLabel FILTER(LANG(?castLabel) = 'en')
      }}
      OPTIONAL {{ ?film wdt:P58 ?screenwriter. }}
      OPTIONAL {{ ?director wikibase:sitelinks ?directorSitelinks. }}
      OPTIONAL {{ ?director wikibase:statements ?directorStatements. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    ORDER BY ?director ?film ?castOrder
    LIMIT {limit}
    OFFSET {offset}
    """


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min_year", type=int, default=2008)
    parser.add_argument("--target", type=int, default=3000)
    parser.add_argument("--page_size", type=int, default=500)
    parser.add_argument("--cache_dir", default="data/cache/wikidata")
    parser.add_argument("--checkpoint", default="data/cache/bootstrap_checkpoint.json")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    checkpoint = load_checkpoint(args.checkpoint) if args.resume else None
    directors: Dict[str, dict] = checkpoint.get("directors", {}) if checkpoint else {}
    films: Dict[str, dict] = checkpoint.get("films", {}) if checkpoint else {}
    actors: Dict[str, dict] = checkpoint.get("actors", {}) if checkpoint else {}
    edges: List[dict] = checkpoint.get("edges", []) if checkpoint else []

    offset = checkpoint.get("offset", 0) if checkpoint else 0
    pages = math.ceil(args.target * 3 / args.page_size)
    current_year = datetime.utcnow().year

    while offset < pages * args.page_size:
        query = build_query(args.min_year, args.page_size, offset)
        data = fetch_sparql(query, args.cache_dir)
        results = data.get("results", {}).get("bindings", [])
        if not results:
            break

        for row in results:
            film_id = row["film"]["value"].split("/")[-1]
            director_id = row["director"]["value"].split("/")[-1]
            sitelinks = int(row.get("directorSitelinks", {}).get("value", 0))
            statements = int(row.get("directorStatements", {}).get("value", 0))
            fame_proxy = sitelinks if sitelinks > 0 else statements

            director = directors.setdefault(
                director_id,
                {
                    "id": director_id,
                    "name": row.get("directorLabel", {}).get("value"),
                    "last_feature_directed_year": None,
                    "recent_features": [],
                    "lane_fingerprint": {lane: 0.0 for lane in LANES},
                    "assignment_score": 0.0,
                    "cast_adjacency_top": [],
                    "fame_proxy": fame_proxy,
                },
            )
            director["fame_proxy"] = max(director.get("fame_proxy", 0), fame_proxy)

            film = films.setdefault(
                film_id,
                {
                    "id": film_id,
                    "title": row.get("filmLabel", {}).get("value"),
                    "year": int(row["year"]["value"]),
                    "director_id": director_id,
                    "genres_raw": set(),
                    "cast": {},
                    "screenwriters": set(),
                },
            )

            if row.get("genreLabel"):
                film["genres_raw"].add(row["genreLabel"]["value"])

            if row.get("screenwriter"):
                film["screenwriters"].add(row["screenwriter"]["value"].split("/")[-1])

            actor_value = row.get("cast", {}).get("value")
            if actor_value:
                actor_id = actor_value.split("/")[-1]
                actor_name = row.get("castLabel", {}).get("value", "Unknown")
                cast_order = row.get("castOrder", {}).get("value")
                order_value = int(cast_order) if cast_order and cast_order.isdigit() else None
                film["cast"][actor_id] = {
                    "id": actor_id,
                    "name": actor_name,
                    "order": order_value,
                }
                actors.setdefault(actor_id, {"id": actor_id, "name": actor_name})

        offset += args.page_size

        save_checkpoint(
            args.checkpoint,
            {
                "offset": offset,
                "directors": directors,
                "films": {
                    key: {
                        **value,
                        "genres_raw": list(value["genres_raw"]),
                        "screenwriters": list(value["screenwriters"]),
                    }
                    for key, value in films.items()
                },
                "actors": actors,
                "edges": edges,
            },
        )

        if len(directors) >= args.target:
            break

    for film in films.values():
        film["genres_raw"] = sorted(set(film["genres_raw"]))
        film["genres_normalized"] = normalize_genres(film["genres_raw"])
        cast_sorted = sorted(
            film["cast"].values(),
            key=lambda member: (member.get("order") is None, member.get("order") or 999, member.get("name")),
        )
        film["top_cast"] = cast_sorted[:8]
        film.pop("cast", None)

    edges = []
    for film in films.values():
        for cast_member in film.get("top_cast", []):
            weight = recency_weight(film["year"], current_year) * billing_weight(cast_member.get("order"))
            edges.append(
                {
                    "director_id": film["director_id"],
                    "actor_id": cast_member["id"],
                    "film_id": film["id"],
                    "year": film["year"],
                    "weight": round(weight, 3),
                }
            )

    directors_filtered = {}
    for director in directors.values():
        director_films = [film for film in films.values() if film["director_id"] == director["id"]]
        director_films = sorted(director_films, key=lambda item: item["year"], reverse=True)
        if not director_films:
            continue
        director["recent_features"] = [
            {
                "film_id": film["id"],
                "title": film["title"],
                "year": film["year"],
                "genres_raw": film["genres_raw"],
                "genres_normalized": film["genres_normalized"],
                "top_cast": film["top_cast"],
            }
            for film in director_films[:8]
        ]
        director["last_feature_directed_year"] = director_films[0]["year"]
        director["lane_fingerprint"] = compute_lane_fingerprint(director["recent_features"])
        director["assignment_score"] = compute_assignment_score(director_films, director["id"])
        directors_filtered[director["id"]] = director

    actors_lookup = {actor_id: actor["name"] for actor_id, actor in actors.items()}
    for director in directors_filtered.values():
        director_edges = [edge for edge in edges if edge["director_id"] == director["id"]]
        director["cast_adjacency_top"] = compute_cast_adjacency(director_edges, actors_lookup)

    output_directors = sorted(directors_filtered.values(), key=lambda item: (item["name"] or "", item["id"]))
    if len(output_directors) < args.target:
        raise RuntimeError(f"Only {len(output_directors)} directors found; expected >= {args.target}.")

    output_films = sorted(films.values(), key=lambda item: (item["year"], item["title"] or "", item["id"]))
    output_actors = sorted(actors.values(), key=lambda item: (item["name"], item["id"]))
    output_edges = sorted(edges, key=lambda item: (item["director_id"], item["actor_id"], item["film_id"]))

    output_directors = output_directors[: args.target]

    with open("data/baseline/directors.json", "w", encoding="utf-8") as handle:
        json.dump(output_directors, handle, indent=2, ensure_ascii=False)
    with open("data/baseline/actors.json", "w", encoding="utf-8") as handle:
        json.dump(output_actors, handle, indent=2, ensure_ascii=False)
    with open("data/baseline/films.json", "w", encoding="utf-8") as handle:
        json.dump(output_films, handle, indent=2, ensure_ascii=False)
    with open("data/baseline/edges_actor_director.json", "w", encoding="utf-8") as handle:
        json.dump(output_edges, handle, indent=2, ensure_ascii=False)

    print(f"Wrote {len(output_directors)} directors, {len(output_films)} films, {len(output_actors)} actors")


if __name__ == "__main__":
    main()
