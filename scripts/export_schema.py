"""Export actual app OpenAPI then prune components by reachable schema references."""

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from cv_api.app import create_app
from cv_foundation.ai_contract import create_contract_app
from cv_foundation.settings import Component, Profile, load_settings


def partition(document: dict[str, Any], tags: set[str]) -> dict[str, Any]:
    result = copy.deepcopy(document)
    result["paths"] = {
        path: {
            method: value for method, value in methods.items() if set(value.get("tags", [])) & tags
        }
        for path, methods in document["paths"].items()
    }
    result["paths"] = {path: methods for path, methods in result["paths"].items() if methods}
    reachable: dict[str, dict[str, Any]] = {}
    visited: set[str] = set()

    def references(value: Any) -> None:
        if isinstance(value, dict):
            ref = value.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/components/") and ref not in visited:
                visited.add(ref)
                _, _, group, key = ref.split("/")
                component = document["components"][group][key]
                reachable.setdefault(group, {})[key] = component
                references(component)
            for child in value.values():
                references(child)
        elif isinstance(value, list):
            for child in value:
                references(child)

    references(result["paths"])
    if tags & {"staff", "local-ai"}:
        reachable["securitySchemes"] = document.get("components", {}).get("securitySchemes", {})
    result["components"] = reachable
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Profile)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    settings = load_settings(args.config, args.profile, Component.API)
    full = create_app(settings).openapi()
    docs = {
        "full": full,
        "staff": partition(full, {"staff", "system"}),
        "public": partition(full, {"public"}),
        "configuration": partition(full, {"contract"}),
        "local-ai": create_contract_app().openapi(),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    for name, document in docs.items():
        (args.output / f"{name}.openapi.json").write_text(
            json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
