# 🏛️ GovContractFinder

An automated government contract finder and intelligence scorecard engine that queries **SAM.gov** daily at **5:00 PM EST** for new or updated solicitations, computes an **Executable Work Scorecard** against a configurable **Skill Sets File**, generates executive summaries of work, and delivers the results through a mobile-accessible responsive web application.

---

## ⚡ Core Features

1. **Daily Automated SAM.gov Query (5:00 PM EST)**:
   - Built-in background cron scheduler (`APScheduler`) configured to run every day at 17:00 EST (`America/New_York`).
   - Fetches newly posted and updated solicitations from the official SAM.gov Opportunities API.
   - Provides live countdown timer and instant on-demand **"Sync Now"** trigger in the UI.

2. **Skill Sets File & Executable Work Scorecard**:
   - Governed by `data/skills.json` (defaults to **Technology**, **Data Analysis**, and **Software Development**).
   - Computes a multi-factor score (0–100%) and tier (**High Match** $\ge 70\%$, **Moderate** $40-69\%$, **Low** $<40\%$).
   - Scores consider:
     - Keyword density and presence in title & description
     - NAICS code alignment (e.g., 541511, 541512, 518210)
     - PSC classification alignment (e.g., DA01, DA10, DB02, DJ01)
     - Deliverable & milestone clarity (SOW, sprints, prototypes, dashboards)
     - Disqualifier detection (penalizes construction, janitorial, or out-of-scope trades)
   - Generates an executive summary of work to be performed and identified deliverables.
   - Includes direct clickable links to the original solicitation on SAM.gov (`https://sam.gov/opp/{noticeId}/view`).

3. **Mobile-Accessible Web App**:
   - Modern, responsive UI designed for mobile phones (iOS & Android) as well as desktop and tablet screens.
   - Safe-area insets, touch-friendly navigation, quick-filter pills, and search bar.
   - Comprehensive Scorecard Deep-Dive Sheet/Modal.
   - Skill Sets editor right in the web app to tweak weights, keywords, and recalculate all scorecards on the fly.
   - Bookmarks and favorites system.

4. **Zero-Configuration Out-of-the-Box Experience**:
   - Ships with realistic mock federal solicitations (DISA, VA, NIH, NASA, CISA, GSA) and control items (construction/janitorial) for immediate testing.
   - Add your free SAM.gov API key anytime via the UI Settings modal or `.env` file to switch to live SAM.gov API ingestion.

---

## 📁 Project Structure

```text
gov-contract-finder/
├── data/
│   ├── contracts.db        # SQLite database (solicitations, scorecards, sync history)
│   └── skills.json         # Default Skill Sets File (Technology, Data Analysis, Software Dev)
├── backend/
│   ├── config.py           # Configuration and environment settings
│   ├── database.py         # SQLite models, indexes, queries, and migrations
│   ├── sam_client.py       # SAM.gov API client with simulation fallback
│   ├── scoring_engine.py   # Multi-factor executable work calculator & summarizer
│   ├── scheduler.py        # APScheduler cron (Daily 5:00 PM EST)
│   └── app.py              # FastAPI REST API & static file server
├── frontend/
│   ├── index.html          # Mobile-first responsive single-page web app
│   ├── app.js              # Client state, dynamic scorecard modals, filters, sync
│   └── styles.css          # Mobile styling, touch-targets, custom score badges
├── .env.example            # Environment variables template
├── run.py                  # Server and scheduler launcher script
└── requirements.txt        # Python package dependencies
```

---

## 🚀 Quick Start

### 1. Launching the Application
From the `gov-contract-finder` folder, run:

```bash
# Using uv (fastest)
uv run python run.py

# Or activate the virtualenv:
.\.venv\Scripts\activate
python run.py
```

### 2. Accessing the Web App
- **Desktop**: Open [http://localhost:8000](http://localhost:8000) in your browser.
- **Mobile Access**: Connect your mobile phone to the same local Wi-Fi network and open `http://<YOUR_LOCAL_IP>:8000` (the exact IP is displayed in the terminal banner when launching `run.py`).

---

## ⚙️ Configuring Your SAM.gov API Key

1. Sign up for a free official API key at [SAM.gov](https://sam.gov/) or [api.data.gov/signup](https://api.data.gov/signup/).
2. Open the web app and click the **Settings (gear icon)** in the top right header.
3. Paste your API key and click **Save API Key**.
4. The system will save the key to `.env` and immediately begin using the live SAM.gov Opportunities API for daily 5:00 PM EST queries and manual syncs!

---

## 🎯 Customizing the Skill Sets File

The scoring criteria live in `data/skills.json`. You can edit this file directly or click the **Sliders icon** in the web app:

```json
{
  "categories": [
    {
      "id": "software_development",
      "name": "Software Development",
      "weight": 0.40,
      "keywords": ["software development", "web application", "api", "microservices", "python", "react", "docker", "kubernetes", "devsecops"],
      "naics": ["541511", "541512", "541519"]
    },
    {
      "id": "data_analysis",
      "name": "Data Analysis & AI",
      "weight": 0.35,
      "keywords": ["data analysis", "data analytics", "machine learning", "power bi", "sql", "predictive modeling", "etl", "data pipeline"],
      "naics": ["541512", "518210", "541715"]
    },
    {
      "id": "technology",
      "name": "Technology & Infrastructure",
      "weight": 0.25,
      "keywords": ["information technology", "cloud computing", "aws", "azure", "cybersecurity", "zero trust", "fedramp"],
      "naics": ["541513", "541519", "518210"]
    }
  ]
}
```

Whenever you save changes in the web app, all solicitations are automatically recalculated against your updated parameters.
