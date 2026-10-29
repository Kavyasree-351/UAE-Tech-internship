"""
Build Markdown Module for UAE Tech & Product Roles Catalog.

Generates:
1. README.md: High-level dashboard, statistical breakdown, badges, and featured listings.
2. INTERNSHIPS.md: Comprehensive, searchable catalog formatted as a clean Markdown table.
"""

import os
import json
import logging
from collections import Counter
from datetime import datetime, timezone
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_jobs_data(json_path: str = "data/internships.json") -> List[Dict[str, Any]]:
    """Load validated jobs from JSON file."""
    if not os.path.exists(json_path):
        logger.warning(f"File {json_path} does not exist. Returning empty list.")
        return []
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
            if isinstance(jobs, list):
                return jobs
    except Exception as e:
        logger.error(f"Error reading {json_path}: {e}")
    return []


def generate_readme(jobs: List[Dict[str, Any]], output_path: str = "README.md") -> None:
    """Generate high-level README dashboard with metrics, breakdown, and highlights."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total_jobs = len(jobs)

    # Category counts
    category_counts = Counter(j.get("category", "Early Career (0-2 yrs)") for j in jobs)
    internship_count = category_counts.get("Internship", 0)
    grad_count = category_counts.get("Graduate Program", 0)
    early_count = category_counts.get("Early Career (0-2 yrs)", 0)

    # Discipline counts
    disc_counts = Counter(j.get("discipline", "Software Engineering") for j in jobs)
    swe_count = disc_counts.get("Software Engineering", 0)
    ai_count = disc_counts.get("AI & Data", 0)
    pm_count = disc_counts.get("Product Management (APM)", 0)
    quant_count = disc_counts.get("Quant", 0)

    # Top companies
    top_companies = [c for c, _ in Counter(j.get("company", "Tech") for j in jobs).most_common(8)]
    companies_str = ", ".join(f"`{c}`" for c in top_companies) if top_companies else "`Careem`, `Delivery Hero`, `Point72`, `Bybit`, `Binance`"

    # Featured latest 10 jobs
    # Sort by date_posted descending
    sorted_jobs = sorted(
        jobs,
        key=lambda x: str(x.get("date_posted", "")),
        reverse=True
    )
    featured = sorted_jobs[:10]

    readme_content = f"""# 🇦🇪 UAE Tech Internships & Early-Career Opportunities

[![Auto-Sync Tech Listings](https://github.com/Kavyasree-Nunna/interns-jobs/actions/workflows/auto_sync.yml/badge.svg)](https://github.com/Kavyasree-Nunna/interns-jobs/actions/workflows/auto_sync.yml)
![Active Opportunities](https://img.shields.io/badge/Active%20Positions-{total_jobs}-brightgreen)
![Target Region](https://img.shields.io/badge/Region-Dubai%20%7C%20Abu%20Dhabi%20%7C%20UAE-blue)
![Last Synchronized](https://img.shields.io/badge/Last%20Updated-{today}-orange)

> **Curated directory of Software Engineering, AI/ML, Data Science, Quantitative Trading, and Associate Product Management (APM) opportunities for university students and fresh graduates (0–2 years) across the United Arab Emirates.**

---

## 📊 Live Market Dashboard

| Metric | Count | Highlight Disciplines & Levels |
| :--- | :--- | :--- |
| **Total Active Opportunities** | **`{total_jobs}`** | Across Dubai, Abu Dhabi, Sharjah & UAE-Remote |
| 🎓 **Internships** | `{internship_count}` | Summer, Winter, Off-Cycle, and Co-op placements |
| 🚀 **Graduate Schemes / Traineeships** | `{grad_count}` | Structured rotational & graduate cohorts |
| 💼 **Early Career (0–2 yrs)** | `{early_count}` | Junior / Associate entry-level roles |
| 💻 **Software Engineering** | `{swe_count}` | Backend, Frontend, Full Stack, Mobile, DevOps, SRE |
| 🤖 **AI & Data Science** | `{ai_count}` | Machine Learning, GenAI, Data Analytics |
| 📱 **Product Management (APM)** | `{pm_count}` | Associate PM, Technical Product Analyst |
| 📈 **Quantitative Trading** | `{quant_count}` | Quant Dev, Algo Trading, Financial Engineering |

**Top Hiring Employers in UAE:**  
{companies_str}

---

## ⚡ Featured & Recent Openings

| Company | Role Title | Category | Discipline | Location | Apply |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""

    if featured:
        for job in featured:
            comp = job.get("company", "Tech Company")
            title = job.get("title", "")
            cat = job.get("category", "Early Career")
            disc = job.get("discipline", "Software Engineering")
            loc = job.get("location", "Dubai, UAE")
            url = job.get("url", "#")
            readme_content += f"| **{comp}** | {title} | `{cat}` | {disc} | {loc} | [Apply ↗]({url}) |\n"
    else:
        readme_content += "| *Updating listings...* | Please check back shortly | — | — | Dubai, UAE | — |\n"

    readme_content += f"""
👉 **[Browse Full Searchable Directory ({total_jobs} Roles) in INTERNSHIPS.md →](./INTERNSHIPS.md)**

---

## 🎯 Target Scope & Disciplines

This repository tracks early-career opportunities in the UAE:

1. **Software Engineering**:
   - Backend (Python, Go, Java, Node.js, C++)
   - Frontend & Mobile (React, TypeScript, iOS, Android, Flutter)
   - Systems, DevOps, Cloud Infrastructure, & SRE
2. **AI & Data Science**:
   - Machine Learning Engineers, Deep Learning, & GenAI/LLM developers
   - Data Analysts, BI Engineers, and Data Scientists
3. **Product Management (APM)**:
   - Associate Product Managers (APM), Technical Product Analysts, PM Interns
4. **Quantitative Engineering & Trading**:
   - Quantitative Researchers, Quant Developers, and Algorithmic Trading Analysts

---

## 🤖 Automated Architecture

```
┌─────────────────────────────────┐
│   Official ATS APIs & JobSpy    │
│  (Greenhouse, Lever, SmartRec,  │
│   LinkedIn / Indeed Dubai)      │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Gemini 2.5 Flash Agentic      │
│  - Filters out >2 yrs roles     │
│  - Verifies UAE physical/remote │
│  - Categorizes & classifies     │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   GitHub Actions (Every 6 hrs)  │
│  - Prunes expired (>30 days)    │
│  - Auto-updates README.md &     │
│    INTERNSHIPS.md               │
└─────────────────────────────────┘
```

---

## 🛠️ Local Development & Manual Run

1. Clone this repository:
   ```bash
   git clone https://github.com/Kavyasree-Nunna/interns-jobs.git
   cd interns-jobs
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run pipeline:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"  # Optional: high-precision AI filter
   python main.py
   ```

---

## 🤝 Contributing & Submitting a Role

Know of a tech internship or graduate program in Dubai/UAE that should be listed?
- Feel free to open an **[Issue](https://github.com/Kavyasree-Nunna/interns-jobs/issues)** or submit a **Pull Request**.
- If your company uses Greenhouse, Lever, or SmartRecruiters, add your board token to `src/fetchers.py`!

*Disclaimer: All job listings and trademarks belong to their respective corporate entities. Direct application links lead directly to official employer career portals.*
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    logger.info(f"Successfully generated {output_path}")


def generate_internships_catalog(jobs: List[Dict[str, Any]], output_path: str = "INTERNSHIPS.md") -> None:
    """Generate the full searchable catalog table in INTERNSHIPS.md."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total_jobs = len(jobs)

    # Sort primarily by date_posted descending, then company
    sorted_jobs = sorted(
        jobs,
        key=lambda x: (str(x.get("date_posted", "")), str(x.get("company", ""))),
        reverse=True
    )

    content = f"""# 🎓 Full Directory: UAE Tech Internships & Early Careers

**Last Synchronized:** `{today}` | **Active Openings:** `{total_jobs}`

> 💡 **Search Tip:** Press `Ctrl + F` (or `Cmd + F` on Mac) to search for specific roles, frameworks, companies, or cities (`Dubai`, `Abu Dhabi`, `Remote`).

---

## 📑 Quick Navigation

- [All Openings Table](#-all-openings-catalog)
- [Software Engineering Roles](#-software-engineering)
- [AI & Data Science Roles](#-ai--data-science)
- [Product Management (APM) Roles](#-product-management-apm)
- [Quantitative Engineering & Trading](#-quantitative-engineering--trading)

---

## 💼 All Openings Catalog

| Company | Role Title | Category | Discipline | Location | Apply Link | Date Posted |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""

    for job in sorted_jobs:
        comp = job.get("company", "Tech Company").replace("|", "-")
        title = job.get("title", "").replace("|", "-")
        cat = job.get("category", "Early Career (0-2 yrs)")
        disc = job.get("discipline", "Software Engineering")
        loc = job.get("location", "Dubai, UAE").replace("|", "-")
        url = job.get("url", "#")
        date_p = job.get("date_posted", "Recently")

        content += f"| **{comp}** | {title} | `{cat}` | {disc} | {loc} | [Apply ↗]({url}) | {date_p} |\n"

    # Category-specific sections for deeper readability
    disciplines = [
        ("💻 Software Engineering", "Software Engineering"),
        ("🤖 AI & Data Science", "AI & Data"),
        ("📊 Product Management (APM)", "Product Management (APM)"),
        ("📈 Quantitative Engineering & Trading", "Quant"),
    ]

    for section_title, disc_name in disciplines:
        disc_jobs = [j for j in sorted_jobs if j.get("discipline") == disc_name]
        content += f"\n---\n\n### {section_title} ({len(disc_jobs)} Roles)\n\n"
        if not disc_jobs:
            content += f"*No active {disc_name} roles currently listed. New roles are ingested every 6 hours.*\n"
            continue

        content += "| Company | Role Title | Level | Location | Apply | Posted |\n"
        content += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for j in disc_jobs:
            c = j.get("company", "Tech")
            t = j.get("title", "")
            cat = j.get("category", "Early Career")
            loc = j.get("location", "Dubai, UAE")
            u = j.get("url", "#")
            d = j.get("date_posted", "Recently")
            content += f"| **{c}** | {t} | `{cat}` | {loc} | [Apply ↗]({u}) | {d} |\n"

    content += """
---

*Automated by [GitHub Actions](https://github.com/Kavyasree-Nunna/interns-jobs/actions) and Gemini 2.5 Flash.*
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Successfully generated {output_path}")


def generate_markdown_catalog(json_path: str = "data/internships.json") -> None:
    """Orchestrates generation of both README.md and INTERNSHIPS.md."""
    jobs = load_jobs_data(json_path)
    generate_readme(jobs, "README.md")
    generate_internships_catalog(jobs, "INTERNSHIPS.md")
    logger.info("Markdown documentation generated successfully.")


if __name__ == "__main__":
    generate_markdown_catalog()
