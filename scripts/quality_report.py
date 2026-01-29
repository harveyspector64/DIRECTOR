#!/usr/bin/env python3
import json
import random
from collections import Counter, defaultdict
from datetime import datetime

LANE_COUNT = 2


def build_lane_signature(lane_fingerprint: dict) -> str:
    lanes = sorted(lane_fingerprint.items(), key=lambda item: item[1], reverse=True)
    top = [lane for lane, weight in lanes if weight > 0][:LANE_COUNT]
    if not top:
        return "Unclassified"
    return "/".join(top)


def main() -> None:
    with open("data/baseline/directors.json", "r", encoding="utf-8") as handle:
        directors = json.load(handle)

    now = datetime.utcnow().date().isoformat()
    distribution = Counter()
    lane_signatures = Counter()
    recent_2020 = 0

    for director in directors:
        year = director.get("last_feature_directed_year")
        if year:
            distribution[year] += 1
            if year >= 2020:
                recent_2020 += 1
        lane_signatures[build_lane_signature(director.get("lane_fingerprint", {}))] += 1

    count = len(directors) or 1
    fame_sorted = sorted(directors, key=lambda item: item.get("fame_proxy", 0), reverse=True)
    non_famous_pool = fame_sorted[200:]
    random.seed(42)
    sample = random.sample(non_famous_pool, min(50, len(non_famous_pool)))

    with open("docs/atlas_stats.md", "w", encoding="utf-8") as handle:
        handle.write("# Atlas Stats\n\n")
        handle.write(f"Generated: {now}\n\n")
        handle.write(f"Director count: {len(directors)}\n\n")
        handle.write("## Last feature directed year distribution\n")
        for year in sorted(distribution.keys(), reverse=True):
            handle.write(f"- {year}: {distribution[year]}\n")
        handle.write("\n")
        handle.write(f"% with last_feature_directed_year >= 2020: {round(recent_2020 / count * 100, 2)}%\n\n")
        handle.write("## Top 20 lane fingerprints (by frequency)\n")
        for lane, freq in lane_signatures.most_common(20):
            handle.write(f"- {lane}: {freq}\n")
        handle.write("\n")
        handle.write("## Non-famous coverage sample (excluding top 200 by fame proxy)\n")
        for director in sample:
            handle.write(
                f"- {director['name']} ({director['id']}) — last feature {director.get('last_feature_directed_year')}\n"
            )

    print("Atlas stats written")


if __name__ == "__main__":
    main()
