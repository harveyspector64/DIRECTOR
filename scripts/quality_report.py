#!/usr/bin/env python3
import json
import random
from datetime import datetime, timedelta

from utils import write_json


def main() -> None:
    with open("data/baseline/directors.json", "r", encoding="utf-8") as handle:
        directors = json.load(handle)

    now = datetime.utcnow().date()
    recent_30 = 0
    recent_90 = 0
    availability_distribution = {}
    recent_feature_2020 = 0

    for director in directors:
        last_verified = director.get("availability", {}).get("last_verified")
        if last_verified:
            date_obj = datetime.strptime(last_verified, "%Y-%m-%d").date()
            if date_obj >= now - timedelta(days=30):
                recent_30 += 1
            if date_obj >= now - timedelta(days=90):
                recent_90 += 1
        status = director.get("availability", {}).get("status", "UNKNOWN")
        availability_distribution[status] = availability_distribution.get(status, 0) + 1
        if director.get("last_feature_directed_year", 0) >= 2020:
            recent_feature_2020 += 1

    count = len(directors) or 1
    freshness = {
        "last_run": now.isoformat(),
        "director_count": len(directors),
        "last_verified_30d_percent": round(recent_30 / count * 100, 2),
        "last_verified_90d_percent": round(recent_90 / count * 100, 2),
        "availability_distribution": availability_distribution,
    }

    write_json("public/data/freshness.json", freshness)

    with open("docs/data_freshness.md", "w", encoding="utf-8") as handle:
        handle.write("# Data Freshness\n\n")
        handle.write(f"Last run: {freshness['last_run']}\n\n")
        handle.write(f"Director count: {freshness['director_count']}\n\n")
        handle.write(f"Verified <30d: {freshness['last_verified_30d_percent']}%\n\n")
        handle.write(f"Verified <90d: {freshness['last_verified_90d_percent']}%\n\n")

    sample = random.sample(directors, min(50, len(directors)))
    with open("docs/atlas_stats.md", "w", encoding="utf-8") as handle:
        handle.write("# Atlas Stats\n\n")
        handle.write(f"Director count: {len(directors)}\n\n")
        handle.write(f"% with last_feature_directed_year >= 2020: {round(recent_feature_2020 / count * 100, 2)}%\n\n")
        handle.write("## Sample directors\n")
        for director in sample:
            handle.write(f"- {director['name']} ({director['id']})\n")

    print("Quality report written")


if __name__ == "__main__":
    main()
