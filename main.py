"""
Main Orchestrator for UAE Tech & Product Roles Scraper.

Coordinates:
1. Loading existing historical listings
2. Scraping raw listings from Greenhouse, Lever, SmartRecruiters, and JobSpy
3. AI Agentic classification and filtering using Gemini 2.5 Flash
4. Merging and 30-day retention pruning
5. Persisting data/internships.json
6. Generating README.md dashboard and INTERNSHIPS.md catalog
"""

import os
import re
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from src.fetchers import aggregate_raw_jobs
from src.agent_filter import filter_and_enrich_jobs
from src.build_markdown import generate_markdown_catalog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DATA_FILE = "data/internships.json"
RETENTION_DAYS = 30


def load_existing_jobs(file_path: str = DATA_FILE) -> List[Dict[str, Any]]:
    """Loads existing validated jobs from JSON if available."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                logger.info(f"Loaded {len(data)} existing jobs from {file_path}.")
                return data
    except Exception as e:
        logger.warning(f"Could not load existing jobs from {file_path}: {e}")
    return []


def parse_job_date(date_str: str) -> datetime:
    """Attempts to parse YYYY-MM-DD date, defaulting to current time if unparseable."""
    if not date_str:
        return datetime.now(timezone.utc)
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(date_str))
    if match:
        try:
            return datetime(
                year=int(match.group(1)),
                month=int(match.group(2)),
                day=int(match.group(3)),
                tzinfo=timezone.utc,
            )
        except Exception:
            pass
    return datetime.now(timezone.utc)


def prune_and_merge_jobs(
    existing_jobs: List[Dict[str, Any]],
    new_jobs: List[Dict[str, Any]],
    retention_days: int = RETENTION_DAYS,
) -> List[Dict[str, Any]]:
    """
    Merges newly discovered validated roles with existing listings,
    deduplicating by canonical URL or (company + normalized title),
    and prunes roles older than retention_days.
    """
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=retention_days)
    logger.info(f"Applying {retention_days}-day retention pruning (cutoff date: {cutoff_date.strftime('%Y-%m-%d')})...")

    # Mapping keyed by url and by (company_lower, title_lower)
    merged_map: Dict[str, Dict[str, Any]] = {}
    key_to_id: Dict[tuple, str] = {}

    # Helper to register or update job
    def add_or_update(job: Dict[str, Any], is_new: bool = False):
        url = job.get("url", "").strip()
        comp = job.get("company", "").strip().lower()
        title = job.get("title", "").strip().lower()
        key = (comp, title)

        existing_id = None
        if url and url in merged_map:
            existing_id = url
        elif key in key_to_id:
            existing_id = key_to_id[key]

        date_posted_str = job.get("date_posted", "")
        parsed_dt = parse_job_date(date_posted_str)

        if existing_id:
            # Update existing entry with newer info if applicable
            current_entry = merged_map[existing_id]
            current_dt = parse_job_date(current_entry.get("date_posted", ""))
            if parsed_dt > current_dt:
                current_entry["date_posted"] = job.get("date_posted", current_entry.get("date_posted"))
            # Keep original URL if current was empty
            if not current_entry.get("url") and url:
                current_entry["url"] = url
        else:
            primary_id = url if url else f"{comp}_{title}_{now.timestamp()}"
            job_copy = dict(job)
            if not job_copy.get("date_posted") or job_copy.get("date_posted") == "Recently":
                job_copy["date_posted"] = now.strftime("%Y-%m-%d")
            merged_map[primary_id] = job_copy
            if url:
                key_to_id[key] = primary_id

    # Ingest existing jobs first
    for j in existing_jobs:
        add_or_update(j, is_new=False)

    # Ingest newly fetched validated jobs
    for j in new_jobs:
        add_or_update(j, is_new=True)

    # Filter out entries older than retention cutoff
    retained_jobs: List[Dict[str, Any]] = []
    pruned_count = 0

    for job in merged_map.values():
        posted_dt = parse_job_date(job.get("date_posted", ""))
        if posted_dt >= cutoff_date:
            retained_jobs.append(job)
        else:
            pruned_count += 1

    logger.info(
        f"Pruning complete: Retained {len(retained_jobs)} active positions, "
        f"pruned {pruned_count} positions older than {retention_days} days."
    )

    # Sort descending by date posted
    retained_jobs.sort(key=lambda x: str(x.get("date_posted", "")), reverse=True)
    return retained_jobs


def save_jobs_data(jobs: List[Dict[str, Any]], file_path: str = DATA_FILE) -> None:
    """Save finalized jobs catalog into JSON."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(jobs)} positions to {file_path}.")


def main():
    start_time = datetime.now()
    logger.info("==================================================")
    logger.info("🚀 Starting UAE Tech Internships & Early-Careers Sync")
    logger.info("==================================================")

    # 1. Load existing jobs
    existing_jobs = load_existing_jobs()

    # 2. Scrape raw listings across all ATS & platforms
    logger.info("Phase 1: Aggregating raw positions across Greenhouse, Lever, SmartRecruiters & JobSpy...")
    raw_jobs = aggregate_raw_jobs()
    logger.info(f"Aggregated {len(raw_jobs)} candidate positions from all platforms.")

    # 3. Agentic filtering and classification via Gemini 2.5 Flash
    logger.info("Phase 2: Running AI agentic validation & classification...")
    validated_new_jobs = filter_and_enrich_jobs(raw_jobs)
    logger.info(f"AI Agent approved {len(validated_new_jobs)} early-career tech/product roles.")

    # 4. Retention pruning and merging
    logger.info("Phase 3: Merging with historical listings & applying retention pruning...")
    final_jobs = prune_and_merge_jobs(existing_jobs, validated_new_jobs, retention_days=RETENTION_DAYS)

    # 5. Persist JSON data
    logger.info("Phase 4: Persisting updated catalog to disk...")
    save_jobs_data(final_jobs)

    # 6. Rebuild Markdown files (README.md and INTERNSHIPS.md)
    logger.info("Phase 5: Rebuilding README.md dashboard and INTERNSHIPS.md catalog...")
    generate_markdown_catalog(DATA_FILE)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("==================================================")
    logger.info(f"🎉 Pipeline finished successfully in {elapsed:.2f} seconds!")
    logger.info(f"Total Active Opportunities Cataloged: {len(final_jobs)}")
    logger.info("==================================================")


if __name__ == "__main__":
    main()
