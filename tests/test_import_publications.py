import json

from src.tools.import_publications import import_publications
from src.utils.file_io import read_json


def test_import_publications_writes_registry(tmp_path):
    config_path = tmp_path / "config.json"
    registry_path = tmp_path / "publications_registry.json"
    seed_path = tmp_path / "publication_seeds.json"

    config_path.write_text(
        json.dumps(
            {
                "profile": {
                    "substack_profile_url": "https://substack.com/@aleclavender",
                    "reads_enabled": True,
                },
                "monitoring": {
                    "discovery_mode": "manual_seed",
                    "publications_registry_path": str(registry_path),
                    "publication_seeds_path": str(seed_path),
                },
            }
        ),
        encoding="utf-8",
    )
    seed_path.write_text(
        json.dumps(
            {
                "publications": [
                    {
                        "publication_name": "Macro Notes",
                        "publication_url": "https://marketnotes.substack.com",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    imported_count = import_publications(str(seed_path), config_path=str(config_path))

    registry = read_json(registry_path, default={})
    assert imported_count == 1
    assert "https://marketnotes.substack.com/" in registry["publications"]
