# GameGuard AI — Threat Detection System

> AI-powered behavioral analysis platform for online game security monitoring.  
> Built with Python, MySQL, Flask, and the Claude API.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?style=flat-square&logo=mysql)
![Claude API](https://img.shields.io/badge/Claude-API-green?style=flat-square)
![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)

---

## Overview

GameGuard AI is a cybersecurity project that simulates a real-world threat detection pipeline for online gaming platforms. It monitors player behavior, detects anomalies using AI-generated risk scoring, and presents actionable intelligence through a live web dashboard.

The system identifies threats such as bot automation, multi-account abuse, abnormal action velocity, and suspicious IP patterns — then classifies each user into a risk tier with a 0–100 AI confidence score.

---

## Features

- **Behavioral analysis** — Tracks session data, action velocity, and event patterns per user
- **AI risk scoring** — Integrates with the Claude API to generate natural language threat assessments
- **Live dashboard** — Real-time web interface with filtering, charts, and one-click moderation actions
- **Automated alerting** — Flags critical users and stores structured alerts in MySQL
- **False positive handling** — Analysts can mark detections as false positives directly from the UI
- **Risk distribution charts** — Doughnut and line charts powered by Chart.js

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask |
| Database | MySQL 8.0 |
| AI Analysis | Anthropic Claude API |
| Frontend | HTML5, CSS3, Vanilla JS |
| Charts | Chart.js 4.4 |
| Fonts | Space Mono, DM Sans |

---

## Project Structure

```
GameGuard-AI/
├── app.py                  # Flask server and REST API routes
├── DB.py                   # Database connection, queries, and data seeder
├── python/
│   └── analyzer.py         # Claude API behavioral analysis module
├── templates/
│   └── index.html          # Dashboard frontend
├── sql/
│   └── schema.sql          # MySQL schema (tables + views)
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- MySQL 8.0
- An Anthropic API key (for AI analysis — optional for basic dashboard)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/gameguard-ai.git
cd gameguard-ai
```

### 2. Install dependencies

```bash
pip install flask mysql-connector-python
```

### 3. Set up the database

Open MySQL and run:

```bash
mysql -u root -p < sql/schema.sql
```

### 4. Configure your credentials

Open `DB.py` and update the connection config:

```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "YOUR_PASSWORD_HERE",
    "database": "gameguard",
}
```

### 5. Seed sample data

```bash
python DB.py
```

This generates 20 simulated users with sessions, behavioral events, and AI-generated risk alerts.

### 6. Run the server

```bash
https://sarahajeanh-ai.github.io/gameguard/
```

Open your browser at **http://localhost:5000**

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/api/stats` | Dashboard summary metrics |
| GET | `/api/usuarios?nivel=all` | User list with optional risk filter |
| GET | `/api/alertas` | Recent alerts ordered by AI score |
| GET | `/api/actividad` | Hourly activity data for charts |
| POST | `/api/bloquear/<id>` | Ban a user and confirm their alerts |
| POST | `/api/falso-positivo/<id>` | Reset user risk and mark alerts as FP |

---

## AI Analysis

When the Claude API is active, `analyzer.py` evaluates each user's behavioral profile and returns:

- A **risk score** from 0 to 100
- A **threat classification** (bot, multi-account, velocity anomaly, suspicious IP)
- A **natural language explanation** stored in the database and shown on the dashboard

Without API credits, the system falls back to rule-based scoring using session and event data already stored in MySQL.

---

## Dashboard Preview

The dashboard provides:

- **4 metric cards** — total users, at-risk count, critical count, pending alerts
- **User table** — sortable by risk level with score bars and moderation actions
- **Alerts panel** — real-time feed of the highest-scoring threats
- **Activity chart** — hourly breakdown of total events vs. anomalies (last 7 days)
- **Risk distribution** — doughnut chart showing the breakdown across all risk tiers

---

## Security Notes

This project is built for **educational and portfolio purposes**. It simulates a threat detection environment and does not connect to any real game or player database. All user data is procedurally generated.

Never commit your database credentials or API keys to a public repository. Use environment variables or a `.env` file in production.

---

## Roadmap

- [ ] Environment variable support via `python-dotenv`
- [ ] JWT authentication for the dashboard
- [ ] Export alerts as CSV / PDF report
- [ ] Real-time WebSocket updates
- [ ] Docker deployment setup
