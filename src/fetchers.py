"""
Dynamic Fetchers Module for UAE Tech & Product Roles.

Automatically discovers tech roles across ALL companies in the UAE using:
1. Dynamic JobSpy Multi-Query Scraper across LinkedIn & Indeed (Dynamic across ALL employers in UAE)
2. Dynamic ATS Board Discovery & Probing (Greenhouse, Lever, SmartRecruiters)
"""

import os
import re
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Set, Optional
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 8

# UAE Regional, City, Freezone, and Tech Hub identifiers
UAE_GEO_KEYWORDS = [
    "dubai",
    "abu dhabi",
    "sharjah",
    "ajman",
    "ras al khaimah",
    "fujairah",
    "umm al quwain",
    "difc",
    "adgm",
    "internet city",
    "silicon oasis",
    "dso",
    "jlt",
    "business bay",
    "media city",
    "hub71",
    "uae",
    "u.a.e",
    "united arab emirates",
]

# Relevance keywords for CSE, Product Management, Data Science, and Quant
RELEVANT_DISCIPLINE_KEYWORDS = [
    "software",
    "engineer",
    "developer",
    "frontend",
    "front-end",
    "backend",
    "back-end",
    "full stack",
    "fullstack",
    "mobile",
    "ios",
    "android",
    "devops",
    "sre",
    "cloud",
    "systems",
    "qa",
    "quality assurance",
    "data",
    "machine learning",
    "ml",
    "ai",
    "artificial intelligence",
    "deep learning",
    "nlp",
    "llm",
    "genai",
    "product manager",
    "apm",
    "product analyst",
    "product operations",
    "quant",
    "quantitative",
    "trading",
    "algo",
    "algorithmic",
    "intern",
    "internship",
    "graduate",
    "trainee",
    "junior",
    "associate",
]

# Seed ecosystem tokens to probe alongside dynamically discovered companies
SEED_UAE_ECOSYSTEM_TOKENS = {
    "careem",
    "point72",
    "bybit",
    "binance",
    "crypto",
    "canonical",
    "okx",
    "checkout",
    "deliveryhero",
    "talabat",
    "noon",
    "rain",
    "analog",
    "fireblocks",
    "kraken",
    "instadeep",
    "hub71",
    "propertyfinder",
    "dubizzle",
}


def _is_uae_location(location_str: str) -> bool:
    """Dynamically checks if location is in UAE or Remote-UAE."""
    if not location_str:
        return False
    loc_lower = location_str.lower()
    if any(kw in loc_lower for kw in UAE_GEO_KEYWORDS):
        return True
    # If explicitly marked remote, ensure it is within UAE or MENA/EMEA context
    if "remote" in loc_lower and any(kw in loc_lower for kw in ["uae", "dubai", "mena", "middle east", "emea"]):
        return True
    return False


def _is_candidate_role(title: str, description: str = "") -> bool:
    """Lightweight check to verify role relevance to Tech, Data, PM, or Quant."""
    text = f"{title} {description[:300]}".lower()
    return any(kw in text for kw in RELEVANT_DISCIPLINE_KEYWORDS)


def _format_date(date_val: Any) -> str:
    """Normalizes raw timestamp or date string into YYYY-MM-DD."""
    if not date_val:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    if isinstance(date_val, (int, float)):
        if date_val > 1e11:
            date_val /= 1000.0
        try:
            return datetime.fromtimestamp(date_val, tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    match = re.search(r"\d{4}-\d{2}-\d{2}", str(date_val))
    return match.group(0) if match else datetime.now(timezone.utc).strftime("%Y-%m-%d")


def fetch_linkedin_and_boards_dynamic() -> List[Dict[str, Any]]:
    """
    DYNAMIC SEARCH: Queries LinkedIn and Indeed across ALL registered UAE companies.
    No hardcoded company names required. Dynamically ingests all employers hiring in UAE.
    """
    logger.info("🌐 Searching LinkedIn & Indeed dynamically for ALL UAE companies...")
    jobs: List[Dict[str, Any]] = []

    # Dynamic queries targeting early career and tech/PM roles across the UAE market
    search_queries = [
        "software engineering internship",
        "associate product manager",
        "computer science intern",
        "data analyst intern",
        "machine learning intern",
        "quantitative trader graduate",
        "junior software engineer",
        "graduate engineer program",
    ]

    try:
        from jobspy import scrape_jobs
    except ImportError:
        logger.warning("JobSpy not installed. Skipping dynamic board scraper.")
        return jobs

    locations = ["Dubai, United Arab Emirates", "Abu Dhabi, United Arab Emirates"]

    for loc in locations:
        for query in search_queries:
            try:
                logger.info(f"Querying LinkedIn for '{query}' in '{loc}'...")
                jobs_df = scrape_jobs(
                    site_name=["linkedin"],
                    search_term=query,
                    location=loc,
                    results_wanted=25,
                    hours_old=720,  # 30 days window
                    country_indeed="United Arab Emirates",
                )

                if jobs_df is not None and not jobs_df.empty:
                    for r in jobs_df.to_dict(orient="records"):
                        company = str(r.get("company") or "").strip()
                        title = str(r.get("title") or "").strip()
                        loc_name = str(r.get("location") or loc).strip()
                        url = str(r.get("job_url") or r.get("job_url_direct") or "").strip()
                        desc = str(r.get("description") or "")[:1200]

                        if url and title and company and _is_candidate_role(title, desc):
                            jobs.append({
                                "source": "LinkedIn / Indeed (Dynamic)",
                                "company": company,
                                "title": title,
                                "location": loc_name,
                                "url": url,
                                "description": desc,
                                "date_posted": _format_date(r.get("date_posted")),
                            })
            except Exception as e:
                logger.warning(f"Error scraping '{query}' in '{loc}': {e}")

    logger.info(f"Dynamic LinkedIn search returned {len(jobs)} total jobs.")
    return jobs


def discover_and_fetch_ats_jobs(discovered_companies: Set[str]) -> List[Dict[str, Any]]:
    """
    Dynamically attempts to fetch jobs from Greenhouse, Lever, and SmartRecruiters endpoints 
    using company tokens extracted live from discovered companies + UAE tech ecosystem seed tokens.
    """
    logger.info("⚡ Dynamically probing ATS endpoints for extracted company names...")
    jobs: List[Dict[str, Any]] = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # Generate token candidates from all discovered company names
    tokens_to_probe: Set[str] = set(SEED_UAE_ECOSYSTEM_TOKENS)

    for comp in discovered_companies:
        clean = re.sub(r"[^a-zA-Z0-9]", "", comp.lower())
        if clean and len(clean) >= 3:
            tokens_to_probe.add(clean)
            # Remove common suffixes like inc, llc, tech, com, group, fz, fze, uae
            stem = re.sub(r"(com|inc|llc|tech|technologies|group|solutions|fz|fze|uae|dubai)$", "", clean)
            if stem and len(stem) >= 3:
                tokens_to_probe.add(stem)

    logger.info(f"Probing {len(tokens_to_probe)} candidate company ATS endpoints...")
    probed_tokens = set()

    for token in tokens_to_probe:
        if token in probed_tokens:
            continue
        probed_tokens.add(token)

        # 1. Probe Greenhouse ATS endpoint dynamically
        gh_url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        try:
            res = requests.get(gh_url, headers=headers, timeout=REQUEST_TIMEOUT)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("jobs", []):
                    title = item.get("title", "").strip()
                    loc_obj = item.get("location", {})
                    loc_name = loc_obj.get("name", "") if isinstance(loc_obj, dict) else str(loc_obj)
                    
                    if not loc_name and item.get("offices"):
                        loc_name = ", ".join([o.get("name", "") for o in item.get("offices", []) if isinstance(o, dict)])

                    if _is_uae_location(loc_name) and _is_candidate_role(title):
                        jobs.append({
                            "source": "Greenhouse (Dynamic Discovery)",
                            "company": token.capitalize(),
                            "title": title,
                            "location": loc_name or "Dubai, UAE",
                            "url": item.get("absolute_url"),
                            "description": item.get("content", "")[:1200],
                            "date_posted": _format_date(item.get("updated_at")),
                        })
        except Exception:
            pass

        # 2. Probe Lever ATS endpoint dynamically
        lever_url = f"https://api.lever.co/v0/postings/{token}?mode=json"
        try:
            res = requests.get(lever_url, headers=headers, timeout=REQUEST_TIMEOUT)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    for item in data:
                        title = item.get("text", "").strip()
                        categories = item.get("categories", {}) or {}
                        location = categories.get("location", "")
                        desc = item.get("descriptionPlain", "") or item.get("description", "")

                        if _is_uae_location(location) and _is_candidate_role(title, desc):
                            jobs.append({
                                "source": "Lever (Dynamic Discovery)",
                                "company": token.capitalize(),
                                "title": title,
                                "location": location or "Dubai, UAE",
                                "url": item.get("hostedUrl") or item.get("applyUrl"),
                                "description": desc[:1200],
                                "date_posted": _format_date(item.get("createdAt")),
                            })
        except Exception:
            pass

        # 3. Probe SmartRecruiters ATS endpoint dynamically
        sr_url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings?country=ae&limit=50"
        try:
            res = requests.get(sr_url, headers=headers, timeout=REQUEST_TIMEOUT)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("content", []):
                    title = item.get("name", "").strip()
                    job_id = item.get("id")
                    loc_obj = item.get("location", {}) or {}
                    city = loc_obj.get("city", "Dubai")
                    full_loc = loc_obj.get("fullLocation", "Dubai, UAE")
                    
                    if _is_candidate_role(title):
                        jobs.append({
                            "source": "SmartRecruiters (Dynamic Discovery)",
                            "company": token.capitalize(),
                            "title": title,
                            "location": f"{city}, UAE",
                            "url": f"https://jobs.smartrecruiters.com/{token}/{job_id}",
                            "description": f"Role: {title} at {token.capitalize()} in {full_loc}",
                            "date_posted": _format_date(item.get("releasedDate")),
                        })
        except Exception:
            pass

    logger.info(f"Dynamic ATS probing discovered {len(jobs)} direct ATS jobs.")
    return jobs


def aggregate_raw_jobs() -> List[Dict[str, Any]]:
    """
    Combines dynamic multi-query LinkedIn/Indeed search with dynamic ATS discovery
    and strictly deduplicates by URL and (Company + Title).
    """
    logger.info("🚀 Aggregating all dynamic job sources across ALL UAE companies...")
    
    # 1. Dynamically pull postings across LinkedIn & Indeed for all UAE companies
    linkedin_jobs = fetch_linkedin_and_boards_dynamic()

    # 2. Extract all unique company names dynamically discovered from the UAE market
    discovered_companies = {j["company"] for j in linkedin_jobs if j.get("company")}
    logger.info(f"Extracted {len(discovered_companies)} unique active hiring companies in UAE from job boards.")

    # 3. Dynamically probe Greenhouse, Lever, and SmartRecruiters for these companies
    ats_jobs = discover_and_fetch_ats_jobs(discovered_companies)

    all_jobs = linkedin_jobs + ats_jobs

    # Deduplicate strictly by canonical URL and normalized (Company + Title) key
    deduped: List[Dict[str, Any]] = []
    seen_urls = set()
    seen_keys = set()

    for job in all_jobs:
        url = job.get("url", "").strip()
        comp = job.get("company", "").strip().lower()
        title = job.get("title", "").strip().lower()
        key = (comp, title)

        if url and url in seen_urls:
            continue
        if key in seen_keys:
            continue

        if url:
            seen_urls.add(url)
        seen_keys.add(key)
        deduped.append(job)

    logger.info(f"✅ Deduplication finished! Total unique roles across ALL UAE companies: {len(deduped)}")
    return deduped


if __name__ == "__main__":
    results = aggregate_raw_jobs()
    print(f"Aggregated {len(results)} jobs completely dynamically.")
    for j in results[:5]:
        print(f"[{j.get('source')}] {j.get('company')} - {j.get('title')} ({j.get('location')}) -> {j.get('url')}")
