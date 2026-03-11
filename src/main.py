from __future__ import annotations

import argparse

from dotenv import load_dotenv

from .config_loader import load_config, load_sources
from .logger import setup_logger
from .pipeline import Pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Substack Reads summary pipeline.")
    parser.add_argument("--config", default="config/config.json", help="Path to config.json")
    parser.add_argument("--sources", default="config/sources.json", help="Path to sources.json")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing processed outputs")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    config = load_config(args.config)
    sources = load_sources(args.sources)
    logger = setup_logger(config.logging)
    pipeline = Pipeline(config=config, sources=sources, logger=logger)
    result = pipeline.run(dry_run=args.dry_run)
    logger.info("Pipeline finished with status=%s", result["status"])


if __name__ == "__main__":
    main()

