#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_type(value: Any, schema_type: Any) -> bool:
    if isinstance(schema_type, list):
        return any(is_type(value, t) for t in schema_type)
    mapping = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "object": dict,
        "array": list,
        "null": type(None),
    }
    return isinstance(value, mapping.get(schema_type, object))


def validate_item(schema: dict, data: Any, path: str) -> None:
    schema_type = schema.get("type")
    if schema_type and not is_type(data, schema_type):
        raise ValueError(f"Type mismatch at {path}: expected {schema_type}")

    if schema_type == "object":
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                raise ValueError(f"Missing required key {path}.{key}")
        properties = schema.get("properties", {})
        for key, subschema in properties.items():
            if key in data:
                validate_item(subschema, data[key], f"{path}.{key}")

    if schema_type == "array":
        items_schema = schema.get("items")
        if items_schema:
            for idx, item in enumerate(data):
                validate_item(items_schema, item, f"{path}[{idx}]")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    datasets = {
        "directors": (root / "schemas" / "director.schema.json", root / "data" / "baseline" / "directors.json"),
        "actors": (root / "schemas" / "actor.schema.json", root / "data" / "baseline" / "actors.json"),
        "films": (root / "schemas" / "film.schema.json", root / "data" / "baseline" / "films.json"),
        "edges": (root / "schemas" / "edges_actor_director.schema.json", root / "data" / "baseline" / "edges_actor_director.json"),
    }

    for label, (schema_path, data_path) in datasets.items():
        schema = load_json(schema_path)
        data = load_json(data_path)
        if isinstance(data, list):
            for idx, item in enumerate(data):
                validate_item(schema, item, f"{label}[{idx}]")
        else:
            validate_item(schema, data, label)
        print(f"Validated {label} ({data_path})")

    directors = load_json(root / "data" / "baseline" / "directors.json")
    if len(directors) < 3000:
        raise RuntimeError(f"Director count {len(directors)} is below 3000")

    print("Validation complete")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Validation failed: {exc}")
        sys.exit(1)
