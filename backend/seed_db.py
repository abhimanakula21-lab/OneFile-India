
from datetime import date, timedelta

from app.database import Base, engine, SessionLocal
from app.models import (
    Institution,
    Case,
    CaseLink,
    CaseTransfer,
    CaseAction,
    User,
)

# Create tables if they do not already exist.
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Prevent duplicate seed data when the script is rerun.
    if db.query(Institution).first():
        print("Database already contains data. No new records added.")
    else:
        institutions = [
            Institution(
                institution_id="DEMO-001",
                name="Sunrise Institute of Technology",
                region="South",
                address="Fictional Address A",
            ),
            Institution(
                institution_id="DEMO-002",
                name="Greenfield College of Engineering",
                region="South",
                address="Fictional Address B",
            ),
            Institution(
                institution_id="DEMO-003",
                name="National Valley Institute",
                region="West",
                address="Fictional Address C",
            ),
            Institution(
                institution_id="DEMO-004",
                name="Sunrise Technical College",
                region="East",
                address="Fictional Address D",
            ),
            Institution(
                institution_id="DEMO-005",
                name="Lakeview School of Technology",
                region="North",
                address="Fictional Address E",
            ),
        ]

        db.add_all(institutions)
        db.flush()

        today = date.today()

        case_data = [
            {
                "case_id": "PGRC-1001",
                "institution_id": "DEMO-001",
                "bureau": "PGRC",
                "category": "Infrastructure",
                "source": "Online Grievance Portal",
                "description": "Complaint about laboratory facilities.",
                "status": "Under Review",
                "opened_at": today - timedelta(days=12),
                "due_at": today - timedelta(days=2),
            },
            {
                "case_id": "RB-2001",
                "institution_id": "DEMO-001",
                "bureau": "Regulation Bureau",
                "category": "Compliance",
                "source": "Internal Referral",
                "description": "Review of laboratory compliance.",
                "status": "Investigation Open",
                "opened_at": today - timedelta(days=18),
                "due_at": today + timedelta(days=5),
            },
            {
                "case_id": "PGRC-1002",
                "institution_id": "DEMO-002",
                "bureau": "PGRC",
                "category": "Admissions",
                "source": "Online Grievance Portal",
                "description": "Complaint about admission procedures.",
                "status": "Pending",
                "opened_at": today - timedelta(days=5),
                "due_at": today + timedelta(days=7),
            },
            {
                "case_id": "REG-3001",
                "institution_id": "DEMO-003",
                "bureau": "Regional Office",
                "category": "Documentation",
                "source": "Official Letter",
                "description": "Missing compliance documents.",
                "status": "Pending",
                "opened_at": today - timedelta(days=16),
                "due_at": today - timedelta(days=4),
            },
            {
                "case_id": "PGRC-1003",
                "institution_id": "DEMO-001",
                "bureau": "PGRC",
                "category": "Infrastructure",
                "source": "Official Letter",
                "description": "Concern regarding laboratory facilities.",
                "status": "Pending",
                "opened_at": today - timedelta(days=10),
                "due_at": today + timedelta(days=3),
            },
            {
                "case_id": "RB-2002",
                "institution_id": "DEMO-004",
                "bureau": "Regulation Bureau",
                "category": "Approval",
                "source": "Internal Review",
                "description": "Review of approval documentation.",
                "status": "In Progress",
                "opened_at": today - timedelta(days=8),
                "due_at": today + timedelta(days=4),
            },
            {
                "case_id": "PGRC-1004",
                "institution_id": "DEMO-005",
                "bureau": "PGRC",
                "category": "General Grievance",
                "source": "Online Grievance Portal",
                "description": "Request for clarification on a submitted grievance.",
                "status": "Resolved",
                "opened_at": today - timedelta(days=20),
                "due_at": today - timedelta(days=10),
            },
            {
                "case_id": "REG-3002",
                "institution_id": "DEMO-002",
                "bureau": "Regional Office",
                "category": "Compliance",
                "source": "Internal Referral",
                "description": "Review of institution compliance documents.",
                "status": "Pending",
                "opened_at": today - timedelta(days=3),
                "due_at": today + timedelta(days=9),
            },
            {
                "case_id": "PGRC-1005",
                "institution_id": "DEMO-003",
                "bureau": "PGRC",
                "category": "Admissions",
                "source": "Direct Portal",
                "description": "Complaint concerning an admission process.",
                "status": "Under Review",
                "opened_at": today - timedelta(days=6),
                "due_at": today + timedelta(days=2),
            },
            {
                "case_id": "RB-2003",
                "institution_id": "DEMO-005",
                "bureau": "Regulation Bureau",
                "category": "Compliance",
                "source": "Internal Review",
                "description": "Routine review of compliance records.",
                "status": "Closed",
                "opened_at": today - timedelta(days=30),
                "due_at": today - timedelta(days=15),
            },
            
            {
                "case_id": "PGRC-1006",
                "institution_id": "DEMO-004",
                "bureau": "PGRC",
                "category": "Institution Complaint",
                "source": "Online Grievance Portal",
                "description": "Synthetic demo complaint requiring review alongside the institution approval case.",
                "status": "Under Investigation",
                "opened_at": today - timedelta(days=3),
                "due_at": today + timedelta(days=7),
            },

        ]

        cases = [Case(**item) for item in case_data]
        db.add_all(cases)
        db.flush()

        links = [
            CaseLink(
                source_case_id="PGRC-1001",
                target_case_id="PGRC-1003",
                relationship_type="potential_duplicate",
                review_status="pending_review",
                similarity_score=0.88,
            ),
            CaseLink(
                source_case_id="PGRC-1001",
                target_case_id="RB-2001",
                relationship_type="same_institution_related_case",
                review_status="pending_review",
                similarity_score=None,
            ),
            CaseLink(
                source_case_id="PGRC-1006",
                target_case_id="RB-2002",
                relationship_type="same_institution_related_case",
                review_status="pending_review",
                similarity_score=None,
            ),

        ]
        db.add_all(links)

        transfers = [
            CaseTransfer(
                case_id="PGRC-1002",
                from_bureau="PGRC",
                to_bureau="Regional Office",
                reason="Request for regional review",
                transfer_status="pending",
            )
        ]
        db.add_all(transfers)

        actions = [
            CaseAction(
                case_id="PGRC-1001",
                actor_role="Demo PGRC Officer",
                action_type="case_created",
                details="Synthetic grievance record created.",
            ),
            CaseAction(
                case_id="RB-2001",
                actor_role="Demo Regulation Officer",
                action_type="investigation_opened",
                details="Synthetic regulatory review opened.",
            ),
        ]
        db.add_all(actions)

        users = [
            User(
                username="demo_admin",
                role="admin",
                bureau="All Bureaus",
            ),
            User(
                username="demo_pgrc",
                role="officer",
                bureau="PGRC",
            ),
            User(
                username="demo_regulation",
                role="officer",
                bureau="Regulation Bureau",
            ),
        ]
        db.add_all(users)

        db.commit()

        print("Database created and synthetic records inserted.")
        print(f"Institutions: {len(institutions)}")
        print(f"Cases: {len(cases)}")
        print(f"Potential/related links: {len(links)}")
        print(f"Transfers: {len(transfers)}")
        print(f"Audit actions: {len(actions)}")
        print(f"Demo users: {len(users)}")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
