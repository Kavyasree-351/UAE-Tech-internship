"""
Agent Filter Module for UAE Tech & Product Roles Scraper.

Uses Gemini 2.5 Flash agentic reasoning with structured Pydantic models
to validate UAE location, filter out senior/lead roles (> 2 years experience),
and classify listings into exact categories and disciplines.
"""

import os
import json
import logging
from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Category and Discipline Literal types
RoleCategory = Literal["Internship", "Graduate Program", "Early Career (0-2 yrs)"]
RoleDiscipline = Literal["Software Engineering", "AI & Data", "Product Management (APM)", "Quant"]


class JobClassification(BaseModel):
    """Structured evaluation schema for individual job posting."""
    keep: bool = Field(
        description="True if role is a genuine early-career (0-2 yrs) tech/quant/product role in UAE, False otherwise."
    )
    company: str = Field(description="Cleaned, standardized company name.")
    title: str = Field(description="Cleaned and standardized role title.")
    category: RoleCategory = Field(
        description="Experience level category: 'Internship', 'Graduate Program', or 'Early Career (0-2 yrs)'."
    )
    discipline: RoleDiscipline = Field(
        description="Target discipline: 'Software Engineering', 'AI & Data', 'Product Management (APM)', or 'Quant'."
    )
    location: str = Field(
        description="UAE location (e.g., 'Dubai, UAE', 'Abu Dhabi, UAE', or 'UAE Remote')."
    )
    url: str = Field(description="Direct application or job post URL.")
    date_posted: str = Field(description="Posting date in YYYY-MM-DD format or 'Recently'.")
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Explanation if keep is False (e.g., 'Requires >2 yrs experience', 'Not in UAE', 'Non-tech role')."
    )


class JobClassificationBatch(BaseModel):
    """Batch container for Gemini structured output."""
    evaluated_jobs: List[JobClassification] = Field(
        description="List of evaluated and classified job postings."
    )


# Senior keywords that disqualify roles from early-career classification
SENIOR_KEYWORDS = [
    "senior",
    "sr.",
    "lead",
    "principal",
    "staff",
    "director",
    "head of",
    "vp",
    "vice president",
    "architect",
    "manager of",
    "engineering manager",
]

# Non-technical / out-of-scope title keywords
IRRELEVANT_ROLE_KEYWORDS = [
    "cook",
    "chef",
    "driver",
    "courier",
    "picker",
    "butchery",
    "distribution center",
    "receptionist",
    "accountant",
    "store leadership",
    "fleet specialist",
    "customer service advisor",
    "marketing specialist",
    "brand manager",
]


def _rule_based_fallback_filter(raw_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    High-fidelity heuristic fallback filter used when GEMINI_API_KEY is not configured
    or if API rate limits/network failures occur.
    """
    logger.info("Applying heuristic classification fallback...")
    approved: List[Dict[str, Any]] = []

    for job in raw_jobs:
        title = job.get("title", "").strip()
        title_lower = title.lower()
        company = job.get("company", "Tech Company").strip()
        location = job.get("location", "Dubai, UAE").strip()
        url = job.get("url", "").strip()
        date_posted = job.get("date_posted", "Recently")

        if not url or not title:
            continue

        # Exclude senior and manager roles
        if any(sk in title_lower for sk in SENIOR_KEYWORDS):
            continue

        # Exclude out-of-scope operations / service roles
        if any(ik in title_lower for ik in IRRELEVANT_ROLE_KEYWORDS):
            continue

        # Determine Category
        if any(kw in title_lower for kw in ["intern", "internship", "summer", "winter", "co-op", "student"]):
            category: RoleCategory = "Internship"
        elif any(kw in title_lower for kw in ["graduate", "trainee", "rotational", "fellowship", "future talent", "cadet"]):
            category = "Graduate Program"
        else:
            category = "Early Career (0-2 yrs)"

        # Determine Discipline
        if any(kw in title_lower for kw in ["product manager", "apm", "product analyst", "product operations", "associate product"]):
            discipline: RoleDiscipline = "Product Management (APM)"
        elif any(kw in title_lower for kw in ["data", "machine learning", "ml", "ai", "artificial intelligence", "deep learning", "nlp", "computer vision", "analytics"]):
            discipline = "AI & Data"
        elif any(kw in title_lower for kw in ["quant", "quantitative", "algorithmic", "algo trader"]):
            discipline = "Quant"
        elif any(kw in title_lower for kw in ["software", "developer", "engineer", "frontend", "backend", "full stack", "fullstack", "mobile", "ios", "android", "devops", "cloud", "qa", "quality assurance", "sre", "systems"]):
            discipline = "Software Engineering"
        else:
            # Check description keywords if title was generic (e.g., "Emirati Future Talent Pool")
            desc_lower = job.get("description", "").lower()
            if "software" in desc_lower or "coding" in desc_lower:
                discipline = "Software Engineering"
            elif "data" in desc_lower or "analytics" in desc_lower:
                discipline = "AI & Data"
            elif "product" in desc_lower:
                discipline = "Product Management (APM)"
            else:
                continue

        approved.append({
            "company": company,
            "title": title,
            "category": category,
            "discipline": discipline,
            "location": location,
            "url": url,
            "date_posted": date_posted,
        })

    logger.info(f"Fallback filter approved {len(approved)} roles out of {len(raw_jobs)} candidates.")
    return approved


def _evaluate_batch_with_gemini(
    client: Any,
    batch: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Evaluates a batch of up to 15 jobs using Gemini 2.5 Flash with Pydantic schema."""
    from google.genai import types

    prompt = f"""You are an elite Technical Talent Architect and Early Careers Recruiter specializing in the UAE and Middle East tech ecosystem.

Your mission is to rigorously evaluate, filter, and classify the following list of candidate job postings.

TARGET AUDIENCE & STRICT CRITERIA:
1. Target Region:
   - Must be physically based in or open to the UAE (Dubai, Abu Dhabi, Sharjah, etc.) or explicitly UAE-Remote.
2. Target Experience Level (STRICT):
   - Internships (Summer, Winter, Off-Cycle, Co-ops, Student Programs).
   - Fresh Graduate Programs / Rotational Schemes / Traineeships (0 years experience).
   - Junior / Associate / Early Career roles (strictly 0 to 2 years experience).
   - REJECT senior, lead, principal, staff, VP, or director positions requiring >2 years experience.
3. Target Disciplines (STRICT):
   - "Software Engineering": Backend, Frontend, Full Stack, Mobile, Systems, DevOps, Cloud, SRE, QA/Automation.
   - "AI & Data": ML Engineer, Data Analyst, Data Scientist, GenAI/LLM Engineer, Deep Learning, Analytics.
   - "Product Management (APM)": Associate Product Manager (APM), Technical Product Analyst, PM Intern.
   - "Quant": Quantitative Researcher, Quantitative Developer, Algorithmic Trading Analyst.
4. Out of Scope (REJECT):
   - Non-technical roles (warehouse, butchery, culinary, customer service, generic sales, marketing, non-technical HR, administrative drivers).
   - Senior roles with misleading titles that demand >2 years professional experience in requirements.

Candidate Jobs to Evaluate (JSON):
{json.dumps(batch, indent=2)}

For each job in the input, evaluate whether to keep it (`keep: true`) or reject it (`keep: false`).
Ensure all classifications strictly match the allowed enum choices for `category` and `discipline`.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JobClassificationBatch,
                temperature=0.1,
            ),
        )

        raw_text = response.text
        parsed = json.loads(raw_text)
        
        # Handle parsed format from schema
        job_list = parsed.get("evaluated_jobs", [])
        approved_jobs: List[Dict[str, Any]] = []

        for item in job_list:
            if item.get("keep") is True:
                approved_jobs.append({
                    "company": item.get("company", "Tech Company"),
                    "title": item.get("title", ""),
                    "category": item.get("category", "Early Career (0-2 yrs)"),
                    "discipline": item.get("discipline", "Software Engineering"),
                    "location": item.get("location", "Dubai, UAE"),
                    "url": item.get("url", ""),
                    "date_posted": item.get("date_posted", "Recently"),
                })
            else:
                logger.debug(f"Gemini rejected '{item.get('title')}' at '{item.get('company')}': {item.get('rejection_reason')}")

        return approved_jobs

    except Exception as e:
        logger.error(f"Error during Gemini batch evaluation: {e}")
        # Fallback for this batch
        return _rule_based_fallback_filter(batch)


def filter_and_enrich_jobs(raw_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Main entry point for agentic evaluation.
    Processes jobs in batches using Gemini 2.5 Flash, falling back to rule-based filtering
    if API key is not configured or in case of errors.
    """
    if not raw_jobs:
        logger.info("No raw jobs provided for filtering.")
        return []

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.warning(
            "⚠️ GEMINI_API_KEY environment variable is not set. "
            "Proceeding with high-precision rule-based filtering & classification."
        )
        return _rule_based_fallback_filter(raw_jobs)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Google GenAI client: {e}. Falling back to rule-based.")
        return _rule_based_fallback_filter(raw_jobs)

    logger.info(f"Filtering {len(raw_jobs)} raw jobs using Gemini 2.5 Flash agentic evaluator...")
    all_approved: List[Dict[str, Any]] = []
    
    # Process in batches of 15 jobs to optimize context window and guarantee JSON fidelity
    batch_size = 15
    for i in range(0, len(raw_jobs), batch_size):
        batch = raw_jobs[i : i + batch_size]
        logger.info(f"Evaluating batch {i // batch_size + 1}/{(len(raw_jobs) + batch_size - 1) // batch_size} ({len(batch)} jobs)...")
        approved_batch = _evaluate_batch_with_gemini(client, batch)
        all_approved.extend(approved_batch)

    logger.info(f"AI Agentic filtering complete. {len(all_approved)} valid early-career tech roles approved.")
    return all_approved


if __name__ == "__main__":
    sample_jobs = [
        {
            "source": "SmartRecruiters",
            "company": "Delivery Hero",
            "title": "Software Engineer II - Backend",
            "location": "Dubai, UAE",
            "url": "https://jobs.smartrecruiters.com/sample1",
            "description": "0-2 years of experience in Python or Go. Dubai, UAE.",
            "date_posted": "2026-10-25"
        },
        {
            "source": "Greenhouse",
            "company": "Point72",
            "title": "Quantitative Trading Intern - Summer 2026",
            "location": "Dubai, UAE",
            "url": "https://boards-api.greenhouse.io/sample2",
            "description": "Undergrad / Master student in CSE or Math. Algorithmic trading.",
            "date_posted": "2026-10-20"
        },
        {
            "source": "Lever",
            "company": "Crypto.com",
            "title": "Senior Staff Director of Engineering",
            "location": "Dubai, UAE",
            "url": "https://jobs.lever.co/sample3",
            "description": "10+ years experience required.",
            "date_posted": "2026-10-15"
        }
    ]
    results = filter_and_enrich_jobs(sample_jobs)
    print("Filtered Results:")
    print(json.dumps(results, indent=2))
