# 🇦🇪 UAE Tech Internships & Early-Career Opportunities

[![Auto-Sync Tech Listings](https://github.com/Kavyasree-351/UAE-Tech-internship/actions/workflows/auto_sync.yml/badge.svg)](https://github.com/Kavyasree-351/UAE-Tech-internship/actions/workflows/auto_sync.yml)
![Active Opportunities](https://img.shields.io/badge/Active%20Positions-317-brightgreen)
![Target Region](https://img.shields.io/badge/Region-Dubai%20%7C%20Abu%20Dhabi%20%7C%20UAE-blue)
![Last Synchronized](https://img.shields.io/badge/Last%20Updated-2026-11-04-orange)

> **Curated directory of Software Engineering, AI/ML, Data Science, Quantitative Trading, and Associate Product Management (APM) opportunities for university students and fresh graduates (0–2 years) across the United Arab Emirates.**

---

## 📊 Live Market Dashboard

| Metric | Count | Highlight Disciplines & Levels |
| :--- | :--- | :--- |
| **Total Active Opportunities** | **`317`** | Across Dubai, Abu Dhabi, Sharjah & UAE-Remote |
| 🎓 **Internships** | `45` | Summer, Winter, Off-Cycle, and Co-op placements |
| 🚀 **Graduate Schemes / Traineeships** | `73` | Structured rotational & graduate cohorts |
| 💼 **Early Career (0–2 yrs)** | `199` | Junior / Associate entry-level roles |
| 💻 **Software Engineering** | `100` | Backend, Frontend, Full Stack, Mobile, DevOps, SRE |
| 🤖 **AI & Data Science** | `158` | Machine Learning, GenAI, Data Analytics |
| 📱 **Product Management (APM)** | `49` | Associate PM, Technical Product Analyst |
| 📈 **Quantitative Trading** | `10` | Quant Dev, Algo Trading, Financial Engineering |

**Top Hiring Employers in UAE:**  
`Jobgether`, `ByteDance`, `Revolut`, `Ghobashgroup`, `Deliveryhero`, `Binance`, `Bybit`, `WSP in the Middle East`

---

## ⚡ Featured & Recent Openings

| Company | Role Title | Category | Discipline | Location | Apply |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MedTourEasy Singapore** | Data Analytics Trainee | `Graduate Program` | AI & Data | United Arab Emirates | [Apply ↗](https://www.linkedin.com/jobs/view/4483058536) |
| **MedTourEasy Jaipur** | Data Analytics Trainee | `Graduate Program` | AI & Data | United Arab Emirates | [Apply ↗](https://www.linkedin.com/jobs/view/4484538597) |
| **MedTourEasy AP** | Data Analyst Trainee | `Graduate Program` | AI & Data | United Arab Emirates | [Apply ↗](https://www.linkedin.com/jobs/view/4484595902) |
| **MedTourEasy Dubai** | Data Analyst Trainee | `Graduate Program` | AI & Data | United Arab Emirates | [Apply ↗](https://www.linkedin.com/jobs/view/4485161567) |
| **Okx** | Associate General Counsel | `Early Career (0-2 yrs)` | AI & Data | Remote Roles - EMEA; Sliema, Malta | [Apply ↗](https://job-boards.greenhouse.io/okx/jobs/8042769003) |
| **Binance** | Binance Accelerator Program - Internal Audit (Technology) | `Internship` | Product Management (APM) | Hong Kong; Singapore; Taiwan; United Arab Emirates | [Apply ↗](https://job-boards.eu.greenhouse.io/binance/jobs/5002254101) |
| **WSP in the Middle East** | Graduate – Artificial Intelligence (Emirati National) | `Graduate Program` | AI & Data | Sharjah, Sharjah Emirate, United Arab Emirates | [Apply ↗](https://www.linkedin.com/jobs/view/4373122430) |
| **Emirates NBD** | UAE National - Software Engineer | `Early Career (0-2 yrs)` | Software Engineering | Dubai, United Arab Emirates | [Apply ↗](https://www.linkedin.com/jobs/view/4485081204) |
| **AAA Global** | Quantitative Researcher | `Early Career (0-2 yrs)` | Quant | Dubai, United Arab Emirates | [Apply ↗](https://www.linkedin.com/jobs/view/4487249461) |
| **CENSUS** | 🚀 CENSUS UAE Cybersecurity Engineering Internship Program: Learn. Hack. Secure! UAE | `Internship` | Software Engineering | Abu Dhabi, Abu Dhabi Emirate, United Arab Emirates | [Apply ↗](https://www.linkedin.com/jobs/view/4487270200) |

👉 **[Browse Full Searchable Directory (317 Roles) in INTERNSHIPS.md →](./INTERNSHIPS.md)**

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
   git clone https://github.com/Kavyasree-351/UAE-Tech-internship.git
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
- Feel free to open an **[Issue](https://github.com/Kavyasree-351/UAE-Tech-internship/issues)** or submit a **Pull Request**.
- If your company uses Greenhouse, Lever, or SmartRecruiters, add your board token to `src/fetchers.py`!

*Disclaimer: All job listings and trademarks belong to their respective corporate entities. Direct application links lead directly to official employer career portals.*
