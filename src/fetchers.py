"""
Fetchers Module for UAE Tech & Product Roles Scraper.

Fetches job openings from:
1. Greenhouse ATS REST API
2. Lever ATS REST API
3. SmartRecruiters ATS REST API
4. JobSpy multi-platform scraper (LinkedIn, Indeed)
"""

import os
import re
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Request timeout in seconds
REQUEST_TIMEOUT = 12

# UAE location identifiers
UAE_LOCATION_KEYWORDS = [
    "dubai",
    "abu dhabi",
    "sharjah",
    "ajman",
    "ras al khaimah",
    "fujairah",
    "umm al quwain",
    "uae",
    "u.a.e",
    "united arab emirates",
]

# Tech, Quantitative, and Product Management discipline keywords
RELEVANT_DISCIPLINE_KEYWORDS = [
    "software",
    "engineer",
    "engineering",
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
    "systems",
    "devops",
    "sre",
    "infrastructure",
    "cloud",
    "data",
    "machine learning",
    "ml",
    "ai",
    "artificial intelligence",
    "deep learning",
    "nlp",
    "computer vision",
    "genai",
    "llm",
    "product manager",
    "product management",
    "apm",
    "product analyst",
    "quant",
    "quantitative",
    "algo",
    "algorithmic",
    "trading",
    "intern",
    "internship",
    "graduate",
    "trainee",
    "junior",
    "associate",
]

# Target top tech employers in UAE with public ATS boards
GREENHOUSE_BOARDS: Dict[str, str] = {
    "careem": "Careem",
    "point72": "Point72",
    "bybit": "Bybit",
    "binance": "Binance",
    "okx": "OKX",
    "canonical": "Canonical",
    "checkout": "Checkout.com",
    "deliveryhero": "Delivery Hero",
    "noon": "Noon",
}

LEVER_BOARDS: Dict[str, str] = {
    "crypto": "Crypto.com",
    "binance": "Binance",
    "rain": "Rain",
    "analog": "Analog",
    "fireblocks": "Fireblocks",
    "kraken": "Kraken",
}

SMARTRECRUITERS_COMPANIES: Dict[str, str] = {
    "DeliveryHero": "Delivery Hero / Talabat",
    "smartrecruiters": "SmartRecruiters",
}


def _is_uae_location(location_str: str) -> bool:
    """Check if location string indicates UAE or UAE-remote."""
    if not location_str:
        return False
    loc_lower = location_str.lower()
    return any(keyword in loc_lower for keyword in UAE_LOCATION_KEYWORDS)


def _is_candidate_role(title: str, description: str = "") -> bool:
    """
    Lightweight heuristic check to ensure role is related to tech,
    data, quantitative engineering, or product management.
    """
    text = f"{title} {description[:300]}".lower()
    return any(kw in text for kw in RELEVANT_DISCIPLINE_KEYWORDS)


def _format_date(date_val: Any) -> str:
    """Format various date inputs into standard YYYY-MM-DD format."""
    if not date_val:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    if isinstance(date_val, (int, float)):
        # Check if timestamp in milliseconds
        if date_val > 1e11:
            date_val /= 1000.0
        try:
            return datetime.fromtimestamp(date_val, tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    str_val = str(date_val).strip()
    match = re.search(r"\d{4}-\d{2}-\d{2}", str_val)
    if match:
        return match.group(0)

    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def fetch_greenhouse_jobs() -> List[Dict[str, Any]]:
    """Fetch active tech and product postings from Greenhouse ATS endpoints."""
    logger.info("Fetching jobs from Greenhouse boards...")
    jobs: List[Dict[str, Any]] = []

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for board_token, company_name in GREENHOUSE_BOARDS.items():
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        try:
            res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if res.status_code != 200:
                continue

            data = res.json()
            for item in data.get("jobs", []):
                loc_obj = item.get("location", {})
                loc_name = loc_obj.get("name", "") if isinstance(loc_obj, dict) else str(loc_obj)
                
                # Check offices array if location name is empty
                if not loc_name and item.get("offices"):
                    loc_name = ", ".join([o.get("name", "") for o in item.get("offices", []) if isinstance(o, dict)])

                title = item.get("title", "").strip()

                if _is_uae_location(loc_name) and _is_candidate_role(title):
                    updated_at = item.get("updated_at")
                    jobs.append({
                        "source": "Greenhouse",
                        "company": company_name,
                        "title": title,
                        "location": loc_name or "Dubai, UAE",
                        "url": item.get("absolute_url"),
                        "description": item.get("content", "")[:1200],
                        "date_posted": _format_date(updated_at),
                    })
        except Exception as e:
            logger.warning(f"Error fetching Greenhouse board '{board_token}': {e}")

    logger.info(f"Greenhouse fetcher found {len(jobs)} candidate roles.")
    return jobs


def fetch_lever_jobs() -> List[Dict[str, Any]]:
    """Fetch active tech and product postings from Lever ATS endpoints."""
    logger.info("Fetching jobs from Lever boards...")
    jobs: List[Dict[str, Any]] = []

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for board_token, company_name in LEVER_BOARDS.items():
        url = f"https://api.lever.co/v0/postings/{board_token}?mode=json"
        try:
            res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if res.status_code != 200:
                continue

            data = res.json()
            if not isinstance(data, list):
                continue

            for item in data:
                categories = item.get("categories", {}) or {}
                location = categories.get("location", "")
                workplace_type = item.get("workplaceType", "")
                
                combined_location = f"{location} {workplace_type}".strip()
                title = item.get("text", "").strip()
                desc = item.get("descriptionPlain", "") or item.get("description", "")

                if _is_uae_location(combined_location) and _is_candidate_role(title, desc):
                    created_at = item.get("createdAt")
                    jobs.append({
                        "source": "Lever",
                        "company": company_name,
                        "title": title,
                        "location": location or "Dubai, UAE",
                        "url": item.get("hostedUrl") or item.get("applyUrl"),
                        "description": desc[:1200],
                        "date_posted": _format_date(created_at),
                    })
        except Exception as e:
            logger.warning(f"Error fetching Lever board '{board_token}': {e}")

    logger.info(f"Lever fetcher found {len(jobs)} candidate roles.")
    return jobs


def fetch_smartrecruiters_jobs() -> List[Dict[str, Any]]:
    """Fetch active tech and product postings from SmartRecruiters REST API."""
    logger.info("Fetching jobs from SmartRecruiters endpoints...")
    jobs: List[Dict[str, Any]] = []

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for company_identifier, company_name in SMARTRECRUITERS_COMPANIES.items():
        # Fetch both general openings and explicit country filter
        urls = [
            f"https://api.smartrecruiters.com/v1/companies/{company_identifier}/postings?country=ae&limit=100",
            f"https://api.smartrecruiters.com/v1/companies/{company_identifier}/postings?limit=100",
        ]

        seen_ids = set()

        for url in urls:
            try:
                res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                if res.status_code != 200:
                    continue

                data = res.json()
                content = data.get("content", [])
                for item in content:
                    job_id = item.get("id")
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    location_obj = item.get("location", {}) or {}
                    city = location_obj.get("city", "")
                    country = location_obj.get("country", "")
                    full_loc = location_obj.get("fullLocation", "")
                    combined_loc = f"{city}, {full_loc} ({country})"

                    is_uae = country.lower() == "ae" or _is_uae_location(combined_loc)

                    title = item.get("name", "").strip()
                    if is_uae and _is_candidate_role(title):
                        job_url = f"https://jobs.smartrecruiters.com/{company_identifier}/{job_id}"
                        released_date = item.get("releasedDate")
                        
                        # Company display refinement (e.g. Talabat vs Delivery Hero)
                        display_company = company_name
                        if "talabat" in title.lower() or "talabat" in combined_loc.lower():
                            display_company = "Talabat"
                        elif "instashop" in title.lower():
                            display_company = "InstaShop"

                        jobs.append({
                            "source": "SmartRecruiters",
                            "company": display_company,
                            "title": title,
                            "location": city or "Dubai, UAE",
                            "url": job_url,
                            "description": f"Role: {title} at {display_company} in {city}, UAE.",
                            "date_posted": _format_date(released_date),
                        })
            except Exception as e:
                logger.warning(f"Error fetching SmartRecruiters for '{company_identifier}': {e}")

    logger.info(f"SmartRecruiters fetcher found {len(jobs)} candidate roles.")
    return jobs


def fetch_linkedin_and_boards() -> List[Dict[str, Any]]:
    """
    Fetch entry-level and internship tech listings via JobSpy
    across LinkedIn and job boards for Dubai/UAE.
    """
    logger.info("Scraping LinkedIn & Job Boards via JobSpy for UAE tech & product roles...")
    jobs: List[Dict[str, Any]] = []

    search_terms = [
        "software engineering internship",
        "associate product manager",
        "computer science intern",
        "data science graduate",
    ]

    try:
        from jobspy import scrape_jobs
    except ImportError:
        logger.warning("JobSpy not installed or import failed. Skipping JobSpy scraping.")
        return jobs

    for term in search_terms:
        try:
            logger.info(f"Querying JobSpy for search term: '{term}' in Dubai, UAE...")
            jobs_df = scrape_jobs(
                site_name=["linkedin"],
                search_term=term,
                location="Dubai, United Arab Emirates",
                results_wanted=15,
                hours_old=720,  # last 30 days
                country_indeed="United Arab Emirates",
            )

            if jobs_df is not None and not jobs_df.empty:
                records = jobs_df.to_dict(orient="records")
                for r in records:
                    company = str(r.get("company") or "Tech Employer").strip()
                    title = str(r.get("title") or "").strip()
                    loc = str(r.get("location") or "Dubai, UAE").strip()
                    url = str(r.get("job_url") or r.get("job_url_direct") or "").strip()
                    desc = str(r.get("description") or "")[:1200]
                    date_val = r.get("date_posted")

                    if url and title and _is_candidate_role(title, desc):
                        jobs.append({
                            "source": "LinkedIn",
                            "company": company,
                            "title": title,
                            "location": loc,
                            "url": url,
                            "description": desc,
                            "date_posted": _format_date(date_val),
                        })
        except Exception as e:
            logger.warning(f"Error during JobSpy search for term '{term}': {e}")

    logger.info(f"JobSpy scraping fetched {len(jobs)} raw listings.")
    return jobs


def aggregate_raw_jobs() -> List[Dict[str, Any]]:
    """
    Aggregates job postings from all ATS and job board sources.
    Performs URL and Title+Company deduplication.
    """
    logger.info("Starting aggregation of raw jobs across all sources...")
    all_raw: List[Dict[str, Any]] = []

    # 1. Official ATS Endpoints
    all_raw.extend(fetch_greenhouse_jobs())
    all_raw.extend(fetch_lever_jobs())
    all_raw.extend(fetch_smartrecruiters_jobs())

    # 2. LinkedIn / JobSpy scraper
    all_raw.extend(fetch_linkedin_and_boards())

    # Deduplicate by canonical URL and (Company + Title) key
    deduped: List[Dict[str, Any]] = []
    seen_urls = set()
    seen_keys = set()

    for job in all_raw:
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

    logger.info(f"Total aggregated raw candidate jobs after deduplication: {len(deduped)}")
    return deduped


if __name__ == "__main__":
    jobs = aggregate_raw_jobs()
    print(f"Aggregated {len(jobs)} jobs successfully.")
    for j in jobs[:5]:
        print(f"[{j.get('source')}] {j.get('company')} - {j.get('title')} ({j.get('location')}) -> {j.get('url')}")
