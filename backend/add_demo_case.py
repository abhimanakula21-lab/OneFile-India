
from app.database import SessionLocal
from app.models import Case, CaseLink
from datetime import date, timedelta

db = SessionLocal()

try:
    case = db.query(Case).filter_by(case_id="PGRC-1006").first()

    if not case:
        case = Case(
            case_id="PGRC-1006",
            institution_id="DEMO-004",
            bureau="PGRC",
            category="Institution Complaint",
            source="Online Grievance Portal",
            description="Synthetic demo complaint for cross-bureau review.",
            status="Under Investigation",
            opened_at=date.today() - timedelta(days=3),
            due_at=date.today() + timedelta(days=7),
        )
        db.add(case)
        db.flush()

    link = db.query(CaseLink).filter_by(
        source_case_id="PGRC-1006",
        target_case_id="RB-2002",
        relationship_type="same_institution_related_case",
    ).first()

    if not link:
        db.add(CaseLink(
            source_case_id="PGRC-1006",
            target_case_id="RB-2002",
            relationship_type="same_institution_related_case",
            review_status="pending_review",
            similarity_score=None,
        ))

    db.commit()
    print("PGRC-1006 and its case link are saved.")

except Exception:
    db.rollback()
    raise
finally:
    db.close()
