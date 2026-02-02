#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timedelta
from typing import List

from utils import load_yaml, write_json

STATUS_BUSY = {"PREP", "FILMING"}
STATUS_ATTACHED = {"IN_TALKS", "ATTACHED"}
STATUS_POST = {"WRAPPED", "POST"}


def compute_availability(events: List[dict]) -> dict:
    today = datetime.utcnow().date()
    if not events:
        return {
            "status": "LIKELY_OPEN",
            "next_likely_open_window": None,
            "confidence": "low",
            "last_verified": today.isoformat(),
        }
    latest = max(events, key=lambda event: event.get("last_verified", ""))
    status = latest.get("status", "UNKNOWN")
    confidence = latest.get("confidence", "low")
    if status in STATUS_BUSY and confidence in {"med", "high"}:
        return {
            "status": "HARD_BUSY",
            "next_likely_open_window": None,
            "confidence": confidence,
            "last_verified": latest.get("last_verified", today.isoformat()),
        }
    if status in STATUS_ATTACHED:
        return {
            "status": "SOFT_BUSY",
            "next_likely_open_window": None,
            "confidence": confidence,
            "last_verified": latest.get("last_verified", today.isoformat()),
        }
    if status in STATUS_POST:
        return {
            "status": "IN_POST",
            "next_likely_open_window": {
                "start": today.isoformat(),
                "end": (today + timedelta(days=90)).isoformat(),
            },
            "confidence": confidence,
            "last_verified": latest.get("last_verified", today.isoformat()),
        }
    return {
        "status": "UNKNOWN",
        "next_likely_open_window": None,
        "confidence": confidence,
        "last_verified": latest.get("last_verified", today.isoformat()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", default="data/events.json")
    parser.add_argument("--candidates", default="data/staging/events_candidates.json")
    args = parser.parse_args()

    try:
        with open(args.events, "r", encoding="utf-8") as handle:
            events = json.load(handle)
    except FileNotFoundError:
        events = []

    try:
        with open(args.candidates, "r", encoding="utf-8") as handle:
            candidates = json.load(handle)
    except FileNotFoundError:
        candidates = []

    overrides = load_yaml("data/overrides/events.override.yaml") or {}
    merged = {event["id"]: event for event in events}
    for candidate in candidates:
        if candidate["id"] in overrides:
            merged[candidate["id"]].update(overrides[candidate["id"]])
        else:
            merged[candidate["id"]] = candidate

    merged_events = list(merged.values())
    write_json("data/events.json", merged_events)

    with open("data/baseline/directors.json", "r", encoding="utf-8") as handle:
        directors = json.load(handle)

    events_by_director = {}
    for event in merged_events:
        if not event.get("director_id"):
            continue
        events_by_director.setdefault(event["director_id"], []).append(event)

    for director in directors:
        director_events = events_by_director.get(director["id"], [])
        director["current_events"] = [event["id"] for event in director_events]
        director["availability"] = compute_availability(director_events)
        if director_events:
            director["data_freshness"]["last_event_seen"] = max(
                event.get("last_verified", "") for event in director_events
            )

    write_json("data/baseline/directors.json", directors)
    print(f"Merged {len(merged_events)} events")


if __name__ == "__main__":
    main()
