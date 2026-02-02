#!/usr/bin/env python3
import json
from datetime import datetime

from utils import write_json


def main() -> None:
    with open("data/baseline/directors.json", "r", encoding="utf-8") as handle:
        directors = json.load(handle)
    with open("data/baseline/actors.json", "r", encoding="utf-8") as handle:
        actors = json.load(handle)
    try:
        with open("data/events.json", "r", encoding="utf-8") as handle:
            events = json.load(handle)
    except FileNotFoundError:
        events = []

    bundle = {
        "updated_at": datetime.utcnow().date().isoformat(),
        "directors": directors,
        "actors": actors,
        "events": events,
    }

    write_json("public/data/bundle.json", bundle)
    write_json(
        "public/data/index_directors.json",
        [{"id": director["id"], "name": director["name"]} for director in directors],
    )
    print("Bundle built")


if __name__ == "__main__":
    main()
