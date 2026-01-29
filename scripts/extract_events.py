#!/usr/bin/env python3
import argparse
import hashlib
import re
from datetime import datetime
from typing import Dict, List

import requests

from utils import write_json

PATTERNS = [
    (re.compile(r"(?P<director>[A-Z][A-Za-z\-\s]+?)\s+is\s+in\s+talks\s+to\s+direct\s+(?P<title>[^\.]+)", re.IGNORECASE), "IN_TALKS"),
    (re.compile(r"(?P<director>[A-Z][A-Za-z\-\s]+?)\s+attached\s+to\s+direct\s+(?P<title>[^\.]+)", re.IGNORECASE), "ATTACHED"),
    (re.compile(r"(?P<title>[^\.]+)\s+will\s+be\s+directed\s+by\s+(?P<director>[A-Z][A-Za-z\-\s]+)", re.IGNORECASE), "ATTACHED"),
]


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def extract_from_url(url: str) -> List[Dict[str, str]]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = strip_html(response.text)
    events = []
    for pattern, status in PATTERNS:
        for match in pattern.finditer(text):
            director = match.group("director").strip()
            title = match.group("title").strip()
            events.append({
                "director_name": director,
                "project_title": title,
                "status": status,
                "confidence": "low",
                "source_url": url
            })
    return events


def build_id(director_id: str, title: str, outlet: str, published: str) -> str:
    raw = f"{director_id}-{title}-{outlet}-{published}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/staging/events_candidates.json")
    args = parser.parse_args()

    items: List[Dict[str, str]] = []
    for inbox_path in ["data/inbox/news_items.json", "data/inbox/search_items.json"]:
        try:
            with open(inbox_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
                items.extend(payload.get("items", []))
        except FileNotFoundError:
            continue

    candidates = []
    for item in items:
        url = item.get("url")
        if not url:
            continue
        try:
            events = extract_from_url(url)
        except Exception:
            continue
        for event in events:
            candidates.append({
                "id": build_id(event.get("director_name", ""), event.get("project_title", ""), url, event.get("status", "")),
                "director_id": None,
                "director_name": event.get("director_name"),
                "project_title": event.get("project_title"),
                "project_type": "FEATURE",
                "status": event.get("status"),
                "dates": None,
                "confidence": event.get("confidence"),
                "last_verified": datetime.utcnow().date().isoformat(),
                "sources": [
                    {
                        "url": url,
                        "outlet": item.get("source") or "Unknown",
                        "title": item.get("title") or event.get("project_title"),
                        "published_date": item.get("published"),
                        "snippet": None,
                    }
                ],
            })

    write_json(args.output, candidates)
    print(f"Extracted {len(candidates)} event candidates")


if __name__ == "__main__":
    import json
    main()
