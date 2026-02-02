#!/usr/bin/env python3
import argparse
from datetime import datetime, timedelta
import urllib.parse
from typing import List, Dict

import requests

from utils import load_yaml, write_json

QUERY_PHRASES = [
    "set to direct",
    "boards",
    "in talks to direct",
    "attached to direct",
    "wraps production",
]


def search_duckduckgo(query: str, domains: List[str]) -> List[Dict[str, str]]:
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    response = requests.post(url, data=params, timeout=30)
    response.raise_for_status()
    results = []
    for line in response.text.split("\n"):
        if "result__a" in line and "href=" in line:
            start = line.find("href=\"") + 6
            end = line.find("\"", start)
            if start > 5 and end > start:
                link = line[start:end]
                parsed = urllib.parse.urlparse(link)
                if parsed.hostname and any(parsed.hostname.endswith(domain) for domain in domains):
                    results.append({"url": link})
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    args = parser.parse_args()

    config = load_yaml("config/sources.yaml")
    domains = config.get("domains", []) if isinstance(config, dict) else []
    cutoff = datetime.utcnow() - timedelta(days=args.days)

    items: List[Dict[str, str]] = []
    for phrase in QUERY_PHRASES:
        query = f"film director {phrase} site:{' OR site:'.join(domains)}"
        try:
            items.extend(search_duckduckgo(query, domains))
        except Exception:
            continue

    manual_path = "data/inbox/manual_urls.txt"
    try:
        with open(manual_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    items.append({"url": line, "source": "manual"})
    except FileNotFoundError:
        pass

    write_json("data/inbox/search_items.json", {
        "cutoff": cutoff.date().isoformat(),
        "items": items
    })
    print(f"Collected {len(items)} search items")


if __name__ == "__main__":
    main()
