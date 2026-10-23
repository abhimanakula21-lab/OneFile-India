# OneFile-India

**Institution-Centric Case Monitoring and Cross-Bureau Coordination Dashboard**

OneFile India is a hackathon prototype designed to improve the visibility and coordination of institution-related complaints and regulatory cases across multiple bureaus. It combines a unified case dashboard, text-based duplicate detection, advisory alerts, case-transfer tracking, and an audit trail in a single application.

> **Prototype notice:** This project uses synthetic demonstration data. It is not an official AICTE application, is not connected to AICTE's production systems, and does not make official regulatory determinations.

## Problem Statement

When institution-related cases are maintained across different bureaus, reviewers may find it difficult to:

- Obtain a consolidated view of an institution's case history.
- Identify potentially overlapping or duplicate complaints.
- Monitor pending and overdue cases.
- Track case transfers and acknowledgement by receiving bureaus.
- Maintain a traceable record of review and workflow actions.

OneFile India demonstrates a unified interface for addressing these coordination challenges.

## Key Features

### 1. Unified Dashboard
- Overview of total cases, open cases, pending cases, and overdue cases.
- Potential duplicate cases awaiting review.
- Institution count and pending transfer metrics.
- Bureau workload and case-status visualizations.

### 2. Institution-Centric Case Register
- View cases associated with an institution.
- Filter and search case records.
- Review case categories, source, bureau, status, and relevant dates.

### 3. Potential Duplicate Detection
- Compare complaint descriptions using TF-IDF text vectorization and cosine similarity.
- Identify candidate pairs for human review.
- Record reviewer decisions as confirmed duplicates or not duplicates.

**Limitation:** Text similarity is a screening mechanism. Similarity scores do not establish that two complaints refer to the same incident.

### 4. Advisory Cross-Bureau Alerts
- Surface configured potential cross-bureau issues for further review.
- Provide supplementary information to support human assessment.

Alerts are advisory only and do not automatically block institutions or determine regulatory violations.

### 5. Case Transfer Workflow
- Record a transfer request between bureaus.
- Track pending and acknowledged transfers.
- Update the case's assigned bureau following acknowledgement.
- Prevent duplicate pending transfers for the same case.

### 6. Audit History
- Record workflow and duplicate-review actions.
- Associate actions with a demonstration actor role.
- Provide a case-level history for review and traceability.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, JavaScript, CSS |
| Frontend development server | Vite |
| Backend API | Python, FastAPI |
| Database and ORM | SQLite, SQLAlchemy |
| Request validation | Pydantic |
| Duplicate matching | scikit-learn, TF-IDF, cosine similarity |
| API testing | FastAPI Swagger UI |

## Project Structure

```text
OneFile India/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   ├── package.json
│   └── ...
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── matching.py
│   ├── seed_db.py
│   ├── caselink.db
│   └── ...
└── README.md
```

The SQLite database is created locally. The seed script supplies synthetic institutions, cases, and demonstration workflow records.

## Prerequisites

Install the following before running the project:

- Python 3.10 or later.
- Node.js and npm.
- A modern web browser.
- Git (optional, for version control).

## Installation and Setup

### Step 1: Obtain the project

Clone the repository if it has been uploaded to a Git hosting service, or open the existing project directory locally.

```bash
git clone <YOUR_REPOSITORY_URL>
cd OneFile India
```

Replace the placeholder with your actual repository URL. If you already have the project locally, skip the clone command.

### Step 2: Set up the backend

Open a terminal in the `backend` directory.

**Windows PowerShell:**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy scikit-learn rapidfuzz
```

If your project already has a `requirements.txt` file, you can install its dependencies instead:

```powershell
pip install -r requirements.txt
```

### Step 3: Initialize demonstration data

From the `backend` directory, run:

```powershell
python seed_db.py
```

The seed script may skip seeding when institutions already exist. If the database has already been initialized, retain the existing data unless a clean demonstration dataset is specifically needed.

### Step 4: Start the backend

From the `backend` directory, with the virtual environment activated:

```powershell
uvicorn app.main:app --reload
```

Backend API:

- Base URL: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Health endpoint: `http://127.0.0.1:8000/api/health`

Keep this terminal running.

### Step 5: Start the frontend

Open a second terminal in the `frontend` directory:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, typically:

`http://localhost:5173`

Keep both the backend and frontend running.

## API Overview

The backend provides endpoints for the dashboard, institution records, case management, duplicate detection, alerts, transfers, and audit history.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check backend health |
| GET | `/api/dashboard` | Dashboard metrics and chart data |
| GET | `/api/cases` | List and filter cases |
| GET | `/api/cases/{case_id}` | Retrieve an individual case |
| GET | `/api/institutions` | List institutions |
| GET | `/api/institutions/{institution_id}` | View institution information and history |
| GET | `/api/institutions/resolve` | Resolve an institution by name and region |
| GET | `/api/duplicates` | Detect potential duplicate cases |
| POST | `/api/duplicates/review` | Save a duplicate-review decision |
| GET | `/api/cases/{case_id}/risk-alerts` | Retrieve configured advisory alerts |
| GET | `/api/sla/overdue` | List overdue cases |
| POST | `/api/cases/{case_id}/transfer` | Initiate a case transfer |
| POST | `/api/transfers/{transfer_id}/acknowledge` | Acknowledge a pending transfer |
| GET | `/api/cases/{case_id}/audit` | Retrieve case audit history |

Open `/docs` to inspect the request schemas and test available endpoints. Exact behavior depends on the implementation in `backend/app/main.py`.

## Demonstration Scenario

A sample demonstration can follow these steps:

1. Open the dashboard and review the workload metrics.
2. Select synthetic institution `DEMO-001`.
3. Inspect related case records, including `PGRC-1001` and `PGRC-1003`.
4. Run duplicate detection and inspect the candidate similarity score.
5. Record a reviewer decision and verify the updated review status.
6. Inspect the case audit history.
7. Review the previously acknowledged transfer for `PGRC-1002`.
8. Demonstrate the advisory-alert panel and explain its configured conditions.

The identifiers and records are illustrative and should not be interpreted as actual AICTE case records.

## Limitations

- Uses synthetic demonstration records, not official AICTE data.
- Does not provide authenticated integration with official AICTE systems.
- Uses text similarity for candidate detection; semantic and contextual matching require further evaluation.
- Does not replace human review or official regulatory processes.
- Production deployment would require authentication, role-based authorization, secure audit logging, privacy controls, testing, monitoring, and an approved integration strategy.

## Future Enhancements

- Authorized integration with approved case-management systems.
- Role-based access for different bureaus and reviewers.
- More advanced duplicate detection combining text, institution identifiers, dates, and case metadata.
- Configurable service-level deadlines and escalation policies.
- Enhanced audit reporting and downloadable summaries.
- Automated testing, deployment pipelines, and security hardening.
- Evaluation of matching precision and recall using an appropriately labelled dataset.

## Responsible Use

OneFile India is a decision-support prototype. Potential matches and alerts should be reviewed by authorized personnel before any action is taken. A similarity score, an overdue status, or a cross-bureau association is not evidence of misconduct.


