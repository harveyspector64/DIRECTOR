#!/usr/bin/env python3
import argparse
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from typing import List, Dict

import requests

from utils import load_yaml, write_json


def parse_rss(xml_text: str) -> List[Dict[str, str]]:
    root = ET.fromstring(xml_text)
    items = []
    for item in root.findall('.//item'):
        title = item.findtext('title')
        link = item.findtext('link')
        pub_date = item.findtext('pubDate')
        if not title or not link:
            continue
        items.append({"title": title, "url": link, "published": pub_date})
    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    args = parser.parse_args()

    config = load_yaml("config/sources.yaml")
    sources = config.get("sources", []) if isinstance(config, dict) else []
    cutoff = datetime.utcnow() - timedelta(days=args.days)

    all_items: List[Dict[str, str]] = []
    for source in sources:
        if isinstance(source, str):
            continue
        if source.get("type") != "rss":
            continue
        url = source.get("url")
        if not url:
            continue
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        entries = parse_rss(response.text)
        for entry in entries:
            all_items.append(
                {
                    "title": entry["title"],
                    "url": entry["url"],
                    "published": entry.get("published"),
                    "source": source.get("name"),
                }
            )

    write_json("data/inbox/news_items.json", {
        "cutoff": cutoff.date().isoformat(),
        "items": all_items
    })
    print(f"Collected {len(all_items)} news items")


if __name__ == "__main__":
    main()
