from __future__ import annotations

import argparse

from ..config_loader import load_config
from ..processing.publication_registry import PublicationRegistry
from ..utils.dates import now_utc_iso
from ..utils.file_io import read_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import publication seeds into the publication registry.")
    parser.add_argument("seed_path", help="Path to a JSON file containing publication seeds.")
    parser.add_argument("--config", default="config/config.json", help="Path to config.json")
    return parser.parse_args()


def import_publications(seed_path: str, config_path: str = "config/config.json") -> int:
    config = load_config(config_path)
    registry = PublicationRegistry(
        config.monitoring.publications_registry_path,
        expiry_after_days=config.monitoring.publication_expiry_days,
    )
    payload = read_json(seed_path, default={}) or {}
    raw_publications = payload.get("publications", payload if isinstance(payload, list) else [])
    if not isinstance(raw_publications, list):
        raise ValueError("Seed file must be a JSON array or an object with a 'publications' array.")

    imported = registry.import_publications(
        raw_publications,
        discovered_from_profile=str(config.profile.substack_profile_url),
        seen_at=now_utc_iso(),
    )
    registry.save()
    return len(imported)


def main() -> None:
    args = parse_args()
    imported_count = import_publications(args.seed_path, config_path=args.config)
    print(f"Imported {imported_count} publications into the registry.")


if __name__ == "__main__":
    main()
