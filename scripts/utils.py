import json
from typing import Any


def load_yaml(path: str) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError:
        return _basic_yaml_loader(path)
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _basic_yaml_loader(path: str) -> Any:
    """Fallback YAML loader for simple key/list files."""
    with open(path, "r", encoding="utf-8") as handle:
        lines = [line.rstrip() for line in handle if line.strip() and not line.strip().startswith("#")]
    data: dict[str, Any] = {}
    current_key = None
    for line in lines:
        if ":" in line and not line.strip().startswith("-"):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                data[key] = value
                current_key = None
            else:
                data[key] = []
                current_key = key
        elif line.strip().startswith("-") and current_key:
            data[current_key].append(line.strip().lstrip("-").strip())
    return data


def write_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
