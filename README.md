# SKILL2HIRE
## Intelligent Employer–Job Seeker Matchmaking and Verified Employment Connections

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/framework-Flask%203.0+-green.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/tests-19%20passed-success.svg)](#running-tests)
[![Status](https://img.shields.io/badge/deployment-live%20on%205001-brightgreen.svg)](#launching-the-server)

---

## 📌 Executive Summary

**SKILL2HIRE** is an enterprise-grade, full-stack recruitment and employment matchmaking platform tailored to solve the two-sided trust crisis in employment:
1. **For Job Seekers**: Eliminates ghost postings, recruitment fraud, and unverified middlemen by displaying only audited, verified enterprises and providing transparent AI compatibility scores.
2. **For Employers**: Streamlines candidate evaluation using NLP-powered skill parsing, semantic matchmaking, and structured applicant funnels.
3. **For Administrators**: Provides live telemetry on dataset ingestion pipelines, pending corporate verification audits, and community fraud alerts.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technologies & Libraries |
| :--- | :--- |
| **Backend & Web Framework** | Python 3.9+, Flask, Werkzeug, Jinja2 |
| **Database & ORM** | SQLite3 / PostgreSQL compatible, SQLAlchemy ORM, Flask-SQLAlchemy |
| **Authentication & Security** | Flask-Login, Flask-WTF CSRF Protection, Werkzeug Security, OWASP standards |
| **AI & NLP Matchmaking** | Scikit-learn (TF-IDF Vectorization, Cosine Similarity), NumPy, Regex Tokenization |
| **Data Ingestion Pipeline** | Automated ETL pipeline, JSON/CSV schema normalizers, data quality metrics |
| **Frontend & Styling** | Custom Navy/Teal Design System, Bootstrap 5, Bootstrap Icons, Chart.js, Vanilla JS |
| **Automated Testing** | Pytest, Pytest-Flask test client |

---

## 🔑 Pre-Seeded Demonstration Accounts

All accounts come pre-configured with realistic profiles, resumes, postings, and applications:

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Platform Administrator** | `admin@skill2hire.com` | `Admin@12345` | Full administrative control, verification queues, fraud incident response, and dataset pipeline telemetry |
| **Verified Employer (TCS)** | `hr@tataconsultancy.com` | `Employer@12345` | Tata Consultancy Services (MCA CIN & GSTIN verified) |
| **Verified Employer (Infosys)**| `careers@infosys.com` | `Employer@12345` | Infosys Limited (Verified badge, open React jobs) |
| **Verified Employer (Flipkart)**| `talent@flipkart.com` | `Employer@12345` | Flipkart Internet (Verified badge, open AI/ML jobs) |
| **Pending Employer (Apex)** | `hiring@apextech.in` | `Employer@12345` | Apex Tech Labs (Pending verification audit for admin review) |
| **Job Seeker 1** | `rahul.sharma@example.com`| `Seeker@12345` | Senior Python Engineer, uploaded resume, applications submitted |
| **Job Seeker 2** | `priya.patel@example.com` | `Seeker@12345` | Machine Learning Specialist, interview scheduled at Flipkart |
| **Job Seeker 3** | `ananya.singh@example.com`| `Seeker@12345` | Frontend React Architect, employment offer extended by Infosys |

---

## 🚀 Quickstart Guide

### 1. Activate Environment
```bash
cd /Users/dhanjaypatel/.gemini/antigravity-ide/scratch/seva-first-innovation
source venv/bin/activate
```

### 2. Run Data Pipeline & Seed Database
```bash
python scripts/data_pipeline.py
python scripts/seed_database.py
```

### 3. Running Automated Tests
```bash
pytest tests/
```
All 19 automated tests cover authentication, public endpoints, matching algorithms, verification transitions, and application lifecycles.

### 4. Launching the Server
```bash
python run.py
```
Open **[http://127.0.0.1:5001](http://127.0.0.1:5001)** in your browser.

---

## 🔍 Core Features Breakdown

### 🤖 Multimodal AI Matchmaking Engine
- **TF-IDF + Cosine Similarity**: Compares candidate career summaries, headlines, and resume texts against comprehensive job descriptions.
- **Skill Extraction & Normalization**: Categorizes hard and soft skills, computing overlapping vs. missing technical proficiencies.
- **Explainable Scoring**: Displays an overall compatibility score alongside transparent percentage breakdowns (Skills: 40%, Text: 25%, Title: 15%, Experience: 10%, Location: 10%).

### 🛡️ Enterprise Verification Center
- Rigorous background verification checks (CIN, GSTIN, Company PAN, corporate addresses).
- Verified badge rendering across job listings and search cards.
- Multi-step administrative review queue with approval notes and structured rejection logs.

### 📊 Dataset Processing & Quality Telemetry
- ETL ingestion engine in `scripts/data_pipeline.py` normalizing benchmark job records.
- Automated quality reporting (`dataset_import_report.json`, `dataset_quality_report.json`, `dataset_verification_report.json`).
- Live Admin monitoring dashboard at `/admin/dataset-status`.

### 🚨 Community Whistleblower & Fraud Incident Response
- Candidates can flag suspicious postings or third-party fee solicitations.
- Admins inspect incident reports with triage status progression (`pending`, `investigating`, `resolved`, `dismissed`) and internal case notes.
