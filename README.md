# Substack Reads Daily Summary

Python project for GitHub Codespaces that collects the public `Reads` activity from a Substack profile, fetches article content, generates summaries, and stores everything as structured JSON for later dashboards or Markdown digests.

## README Maintenance Rule
Every project change made in this Codespace must also be added to this `README.md` file.

This README is the project update directory and context history. When code, config, tests, structure, pipeline behavior, or setup steps change, add a dated note to the `Change Log` section before closing the task.

## What The Pipeline Does
- Treats the public Substack profile for `@aleclavender` as an optional discovery source
- Supports `live_reads`, `manual_seed`, and `registry_only` discovery modes
- Uses `Reads` as a best-effort discovery layer for publications and any directly visible article links when available
- Monitors discovered publications daily using RSS first with HTML fallback when needed
- Fetches only newly discovered article pages and parses metadata plus article body text
- Deduplicates against prior runs
- Summarizes article text with an LLM API or a local fallback if no API key is configured
- Writes raw, processed, and consumer-facing JSON outputs

## MVP Features
- Single Substack profile source
- Browser-driven Reads scraping with Playwright
- JSON config and JSON data storage
- Daily batch-friendly pipeline
- Canonical URL plus content hash deduplication
- Output files ready for future dashboard or digest rendering

## Repo Structure
```text
config/          User-editable JSON configuration
data/raw/        Raw scraped links, article HTML, and run manifests
data/processed/  Normalized article and summary datasets
data/state/      Dedupe memory and run history
output/latest/   Stable consumer-facing JSON outputs
output/archive/  Dated output snapshots
src/             Application source code
tests/           Unit tests and fixtures
```

## Setup In GitHub Codespaces
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browser binaries:
   ```bash
   python -m playwright install chromium
   ```
4. Copy `.env.example` to `.env` and add `OPENAI_API_KEY` if you want LLM summaries.
5. Update [`config/config.json`](/workspaces/Substack-Market-reviews/config/config.json) with your Substack profile URL.

## Config Files
- [`config/config.json`](/workspaces/Substack-Market-reviews/config/config.json): primary runtime settings
- [`config/sources.json`](/workspaces/Substack-Market-reviews/config/sources.json): optional source registry for future expansion
- [`config/publication_seeds.json`](/workspaces/Substack-Market-reviews/config/publication_seeds.json): optional bootstrap list for manually seeded publication monitoring
- [`data/state/publications_registry.json`](/workspaces/Substack-Market-reviews/data/state/publications_registry.json): persistent publication monitoring registry with expiry and check metadata
- `config.preflight`: DNS and HTTP connectivity checks that run before source monitoring starts

## Running One Pipeline Job
```bash
python -m src.main
```

Optional dry run:
```bash
python -m src.main --dry-run
```

Seed the publication registry manually:
```bash
python -m src.tools.import_publications config/publication_seeds.json
```

Run DNS and HTTP connectivity checks:
```bash
python - <<'PY'
from src.tools.network_checks import dns_check, http_check
print(dns_check())
print(http_check())
PY
```

## Run Health Artifacts
- [`data/latest_run_status.json`](/workspaces/Substack-Market-reviews/data/latest_run_status.json): latest run health summary with `healthy`, `degraded`, or `failed`
- [`data/connectivity_report.json`](/workspaces/Substack-Market-reviews/data/connectivity_report.json): latest DNS and HTTP preflight results
- [`data/latest_articles.json`](/workspaces/Substack-Market-reviews/data/latest_articles.json): most recent run dataset, even if empty or degraded
- [`data/latest_successful_articles.json`](/workspaces/Substack-Market-reviews/data/latest_successful_articles.json): last trustworthy healthy dataset
- [`data/registry.json`](/workspaces/Substack-Market-reviews/data/registry.json): consumer-facing source health snapshot
- `data/run_history/`: per-run status snapshots written by the health wrapper

## Discovery Modes
- `registry_only`: default production mode; skips live Reads scraping and monitors publications already stored in the registry
- `manual_seed`: loads publications from [`config/publication_seeds.json`](/workspaces/Substack-Market-reviews/config/publication_seeds.json) and upserts them into the registry before monitoring
- `live_reads`: attempts live Reads scraping, but challenge pages fail fast and fall back to the existing registry state for monitoring

## GitHub Actions Automation
- Scheduled workflow: [`.github/workflows/daily-pipeline.yml`](/workspaces/Substack-Market-reviews/.github/workflows/daily-pipeline.yml)
- Schedule: once per day at `06:00 AEST` (`20:00 UTC` on the previous day in GitHub Actions cron)
- Pipeline command in CI: `python -m src.main`
- Playwright setup in CI: `python -m playwright install --with-deps chromium`
- Required secret for LLM summaries: `OPENAI_API_KEY`
- The workflow uploads generated data and logs as artifacts and commits updated tracked data files only when a real diff exists.

## Output Files
- [`output/latest/articles_enriched.json`](/workspaces/Substack-Market-reviews/output/latest/articles_enriched.json): latest flat canonical article batch with run metadata
- [`output/latest/daily_digest.json`](/workspaces/Substack-Market-reviews/output/latest/daily_digest.json): digest-oriented grouped output
- `output/latest/daily_digest.md`: GitHub-friendly markdown digest built from the flat daily article batch
- [`output/latest/dashboard_feed.json`](/workspaces/Substack-Market-reviews/output/latest/dashboard_feed.json): flatter dashboard feed

## Data Model Overview
- `ReadItem`: one link discovered from the public Reads page
- `ArticleRecord`: parsed article metadata and full text
- `SummaryRecord`: summary plus summary generation metadata
- `RunManifest`: counts, errors, and timing for one run

## Testing
```bash
pytest
```

Tests use local fixtures and do not require live network access.

## Known Limitations
- Substack markup can change without notice
- Some article bodies may be truncated or blocked by paywalls
- The default scraper uses heuristics for finding Reads links in public pages
- LLM summaries depend on API availability unless fallback mode is used

## Future Improvements
- Multi-source support
- Markdown digest generation
- GitHub Actions daily automation
- Topic tagging and classification
- Retry queue for failed article fetches
- Markdown digest generation wired into the output pipeline

## Change Log

### 2026-03-11
- Initialized the Codespaces project structure for a Python and JSON Substack Reads pipeline.
- Added runtime folders for `config`, `data`, `output`, `logs`, `src`, and `tests`.
- Added starter project files including `.gitignore`, `.env.example`, and `requirements.txt`.
- Created JSON config files at [`config/config.json`](/workspaces/Substack-Market-reviews/config/config.json) and [`config/sources.json`](/workspaces/Substack-Market-reviews/config/sources.json).
- Created starter state and output JSON files under [`data/state`](/workspaces/Substack-Market-reviews/data/state) and [`output/latest`](/workspaces/Substack-Market-reviews/output/latest).
- Implemented the main pipeline modules for config loading, logging, scraping, article extraction, deduplication, summarization, serialization, and output writing under [`src/`](/workspaces/Substack-Market-reviews/src).
- Added the CLI entrypoint at [`src/main.py`](/workspaces/Substack-Market-reviews/src/main.py).
- Implemented Playwright browser setup and a Playwright-first Reads scraper for public Substack profile pages.
- Added scraper behavior to wait for page rendering, collect visible article-like links, normalize and deduplicate URLs, and return `ReadItem` objects.
- Added debug snapshot behavior so failed Reads extraction writes rendered HTML to `data/raw/reads/YYYY-MM-DD_reads_debug.html`.
- Updated the pipeline to log the debug snapshot path when no Reads links are found.
- Added unit tests and HTML fixtures for config loading, normalization, deduplication, article extraction, digest building, and Reads scraping.
- Verified the project with `pytest`, including scraper-specific tests.
- Changed the storage schema from nested `article` plus `summary` output into a flat canonical article record for long-term JSON storage.
- Added canonical fields for `subtitle`, `summary_short`, `summary_bullets`, `key_takeaway`, `topic_tags`, `processing_status`, `summary_status`, and `error_message`.
- Added a daily article batch wrapper with top-level run metadata and an `articles` array for `data/processed/articles/YYYY-MM-DD.json` and `output/latest/articles_enriched.json`.
- Updated digest and dashboard builders to read from flat canonical article records instead of nested article-summary objects.
- Added failure-record support so extraction failures can be written in the same schema as successful articles.
- Updated parser, serializer, model, and output tests to reflect the new flat JSON schema.
- Added a standalone markdown digest module that renders the flat daily JSON article batch into a GitHub-friendly grouped markdown digest.
- Added markdown digest tests and a sample daily batch fixture covering grouping, filtering, ordering, and file output.
- Added a daily GitHub Actions workflow that installs Python, installs Playwright Chromium, runs the daily pipeline, uploads artifacts, and commits changed data files back to the repo only when tracked outputs changed.
- Updated the GitHub Actions schedule to run daily at `06:00 AEST`, which is `20:00 UTC` on the previous day in GitHub Actions cron.
- Refactored the pipeline so the public `Reads` page acts as the publication discovery layer instead of the only article source.
- Added a persistent publication registry in [`data/state/publications_registry.json`](/workspaces/Substack-Market-reviews/data/state/publications_registry.json) with expiry and monitoring metadata.
- Added RSS-first publication monitoring with HTML fallback for tracked publications, and merged monitored posts with any direct Reads article links before deduplication.
- Added monitoring config fields for publication expiry, max publications checked per run, and max posts per publication.
- Added tests and fixtures for publication discovery, publication registry updates/expiry, and RSS feed parsing.
- Corrected the public Substack profile handle from `@alec.lavender` to `@aleclavender` across config, docs, and tests.
- Updated the Reads scraper to fail fast on challenge/interstitial pages and load timeouts, saving a debug snapshot instead of hanging on `networkidle`.
- Added compliant discovery modes so the pipeline can run without live Reads access: `registry_only` as the default, `manual_seed` for bootstrap imports, and `live_reads` as a best-effort option.
- Added [`config/publication_seeds.json`](/workspaces/Substack-Market-reviews/config/publication_seeds.json) plus the import helper `python -m src.tools.import_publications` to populate the publication registry manually.
- Updated the pipeline so daily monitoring can continue from the saved publication registry even when the Reads route is blocked by a challenge page.
- Replaced the placeholder publication seed with Doomberg at [`config/publication_seeds.json`](/workspaces/Substack-Market-reviews/config/publication_seeds.json) and imported it into [`data/state/publications_registry.json`](/workspaces/Substack-Market-reviews/data/state/publications_registry.json).
- Ran the pipeline in `registry_only` mode against the seeded Doomberg publication and confirmed that Reads scraping was skipped as intended.
- Recorded the current live blocker for Doomberg from this environment: DNS resolution for `newsletter.doomberg.com` failed during RSS/homepage monitoring, so the run completed with zero articles and an error status stored on the publication registry entry.
- Added HFI Research to [`config/publication_seeds.json`](/workspaces/Substack-Market-reviews/config/publication_seeds.json) using the provided tracked profile URL and imported it into [`data/state/publications_registry.json`](/workspaces/Substack-Market-reviews/data/state/publications_registry.json) as the normalized publication URL `https://www.hfir.com/`.
- Ran the live pipeline again in `registry_only` mode with both Doomberg and HFI Research in the registry and confirmed the run completed cleanly with zero articles.
- Recorded the current network blocker for both seeded publications from this environment: `newsletter.doomberg.com` and `www.hfir.com` both failed DNS resolution during RSS/homepage monitoring, so both registry entries now show `monitor_status: error` with the captured request exceptions.
- Added reusable network diagnostics in [`src/tools/network_checks.py`](/workspaces/Substack-Market-reviews/src/tools/network_checks.py) with `dns_check()` and `http_check()` helpers for verifying whether DNS resolution and outbound HTTP are working from the current environment.
- Added a run-health wrapper with preflight DNS/HTTP checks, explicit `healthy`/`degraded`/`failed` run classification, and protected latest-output handling.
- Added new orchestration modules for diagnostics, preflight, run-state tracking, status rules, and output guarding under [`src/`](/workspaces/Substack-Market-reviews/src).
- Extended the config schema with a `preflight` section for required DNS hosts, HTTP URLs, and request headers.
- Updated the main entrypoint so it always writes [`data/latest_run_status.json`](/workspaces/Substack-Market-reviews/data/latest_run_status.json) and [`data/connectivity_report.json`](/workspaces/Substack-Market-reviews/data/connectivity_report.json), and only promotes [`data/latest_successful_articles.json`](/workspaces/Substack-Market-reviews/data/latest_successful_articles.json) on healthy runs.
- Added `data_freshness` tagging to latest article payloads and fallback display behavior so degraded empty runs can transparently show the last successful dataset in consumer-facing latest outputs.
- Extended publication registry records with attempt/error metadata and added the derived health snapshot at [`data/registry.json`](/workspaces/Substack-Market-reviews/data/registry.json).
