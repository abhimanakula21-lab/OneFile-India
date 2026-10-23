
from datetime import date, datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import Base, engine, get_db
from app.models import (
    Institution,
    Case,
    CaseLink,
    CaseTransfer,
    CaseAction,
)
from app.matching import (
    resolve_institution,
    detect_duplicate_candidates,
)


# --------------------------------------------------
# 1. Application configuration
# --------------------------------------------------

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AICTE CaseLink API",
    description=(
        "Demonstration API for institution-centric case monitoring, "
        "duplicate-case review, cross-bureau alerts, SLA tracking, "
        "case transfers, and audit history. Uses demo data."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://onefile-india.onrender.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# 2. Shared helpers
# --------------------------------------------------

OPEN_STATUSES = {
    "pending",
    "under review",
    "investigation open",
    "under investigation",
    "in progress",
}


APPROVAL_RENEWAL_CATEGORIES = {
    "approval",
    "renewal",
}


def utc_now():
    return datetime.now(timezone.utc)


def to_iso(value):
    """Convert date/datetime values to ISO strings."""
    return value.isoformat() if value is not None else None


def is_open_status(status):
    return (status or "").strip().lower() in OPEN_STATUSES


def serialize_case(case):
    """Convert a Case database record into JSON-friendly data."""
    today = date.today()

    opened_date = case.opened_at
    if isinstance(opened_date, datetime):
        opened_date = opened_date.date()

    due_date = case.due_at
    if isinstance(due_date, datetime):
        due_date = due_date.date()

    days_pending = (
        (today - opened_date).days
        if opened_date is not None
        else None
    )

    is_overdue = (
        due_date is not None
        and due_date < today
        and is_open_status(case.status)
    )

    return {
        "id": case.id,
        "case_id": case.case_id,
        "institution_id": case.institution_id,
        "bureau": case.bureau,
        "category": case.category,
        "source": case.source,
        "description": case.description,
        "status": case.status,
        "opened_at": to_iso(case.opened_at),
        "due_at": to_iso(case.due_at),
        "created_at": to_iso(case.created_at),
        "days_pending": days_pending,
        "is_overdue": is_overdue,
    }


def serialize_institution(institution):
    return {
        "id": institution.id,
        "institution_id": institution.institution_id,
        "name": institution.name,
        "region": institution.region,
        "address": institution.address,
    }


def serialize_transfer(transfer):
    return {
        "id": transfer.id,
        "case_id": transfer.case_id,
        "from_bureau": transfer.from_bureau,
        "to_bureau": transfer.to_bureau,
        "reason": transfer.reason,
        "transfer_status": transfer.transfer_status,
        "transferred_at": to_iso(transfer.transferred_at),
        "acknowledged_at": to_iso(transfer.acknowledged_at),
    }


def log_action(
    db,
    case_id,
    actor_role,
    action_type,
    details,
):
    action = CaseAction(
        case_id=case_id,
        actor_role=actor_role,
        action_type=action_type,
        details=details,
        created_at=utc_now(),
    )
    db.add(action)
    return action


# --------------------------------------------------
# 3. Request schemas
# --------------------------------------------------

class TransferRequest(BaseModel):
    to_bureau: str = Field(min_length=2, max_length=100)
    reason: str = Field(min_length=5, max_length=1000)


class TransferAcknowledgement(BaseModel):
    actor_role: str = Field(
        default="Demo Receiving Officer",
        min_length=2,
        max_length=100,
    )
class DuplicateReviewRequest(BaseModel):
    case_id_1: str
    case_id_2: str
    decision: str
    actor_role: str = "Demo Reviewer"
    similarity_score: float | None = None


# --------------------------------------------------
# 4. Health check
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "AICTE CaseLink API is running.",
        "demo_data": True,
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "demo_data": True}


# --------------------------------------------------
# 5. Dashboard metrics
# --------------------------------------------------

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    cases = db.query(Case).all()

    total_cases = len(cases)

    open_cases = [
        case for case in cases
        if is_open_status(case.status)
    ]

    overdue_cases = [
        case for case in open_cases
        if case.due_at is not None
        and (
            case.due_at.date()
            if isinstance(case.due_at, datetime)
            else case.due_at
        ) < date.today()
    ]

    pending_duplicate_reviews = (
        db.query(CaseLink)
        .filter(
            CaseLink.relationship_type == "potential_duplicate",
            CaseLink.review_status == "pending_review",
        )
        .count()
    )

    bureau_counts = {}
    for case in cases:
        bureau_counts[case.bureau] = (
            bureau_counts.get(case.bureau, 0) + 1
        )
    
    # Count cases by status for the dashboard visualization.
    status_counts = {}

    for case in cases:
        status = (case.status or "Unknown").strip()
        status_counts[status] = status_counts.get(status, 0) + 1


    return {
        "demo_data": True,
        "total_cases": total_cases,
        "open_cases": len(open_cases),
        "pending_cases": sum(
            1 for case in cases
            if (case.status or "").strip().lower() == "pending"
        ),
        "overdue_cases": len(overdue_cases),
        "potential_duplicates": pending_duplicate_reviews,
        "institutions": db.query(Institution).count(),
        "pending_transfers": (
            db.query(CaseTransfer)
            .filter(CaseTransfer.transfer_status == "pending")
            .count()
        ),
        "cases_by_bureau": bureau_counts,
        "cases_by_status": status_counts,
    }


# --------------------------------------------------
# 6. Case endpoints
# --------------------------------------------------

@app.get("/api/cases")
def list_cases(
    institution_id: str | None = None,
    bureau: str | None = None,
    status: str | None = None,
    overdue_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Case)

    if institution_id:
        query = query.filter(
            Case.institution_id == institution_id
        )

    if bureau:
        query = query.filter(Case.bureau.ilike(bureau.strip()))

    if status:
        query = query.filter(Case.status.ilike(status.strip()))

    cases = query.order_by(Case.opened_at.desc()).all()
    results = [serialize_case(case) for case in cases]

    if overdue_only:
        results = [
            item for item in results
            if item["is_overdue"]
        ]

    return {
        "count": len(results),
        "results": results,
    }


@app.get("/api/cases/{case_id}")
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
):
    case = (
        db.query(Case)
        .filter(Case.case_id == case_id)
        .first()
    )

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    result = serialize_case(case)

    institution = (
        db.query(Institution)
        .filter(
            Institution.institution_id == case.institution_id
        )
        .first()
    )

    result["institution"] = (
        serialize_institution(institution)
        if institution
        else None
    )

    return result


# --------------------------------------------------
# 7. Institution endpoints
# IMPORTANT: static /resolve route must appear before
# the dynamic /{institution_id} route.
# --------------------------------------------------

@app.get("/api/institutions")
def list_institutions(
    db: Session = Depends(get_db),
):
    institutions = (
        db.query(Institution)
        .order_by(Institution.name.asc())
        .all()
    )

    return {
        "count": len(institutions),
        "results": [
            serialize_institution(item)
            for item in institutions
        ],
    }


@app.get("/api/institutions/resolve")
def resolve_institution_api(
    name: str = Query(min_length=1),
    region: str | None = None,
    db: Session = Depends(get_db),
):
    result = resolve_institution(
        db=db,
        institution_name=name,
        region=region,
    )

    institution = result.get("institution")

    return {
        "match_type": result.get("match_type", "no_match"),
        "confidence": result.get("confidence", 0.0),
        "confirmed": result.get("confirmed", False),
        "review_required": result.get(
            "review_required",
            institution is not None
            and not result.get("confirmed", False),
        ),
        "institution": (
            serialize_institution(institution)
            if institution
            else None
        ),
    }


@app.get("/api/institutions/{institution_id}")
def get_institution(
    institution_id: str,
    db: Session = Depends(get_db),
):
    institution = (
        db.query(Institution)
        .filter(
            Institution.institution_id == institution_id
        )
        .first()
    )

    if not institution:
        raise HTTPException(
            status_code=404,
            detail="Institution not found",
        )

    cases = (
        db.query(Case)
        .filter(
            Case.institution_id == institution_id
        )
        .order_by(Case.opened_at.desc())
        .all()
    )

    serialized_cases = [
        serialize_case(case) for case in cases
    ]

    return {
        "institution": serialize_institution(institution),
        "total_cases": len(serialized_cases),
        "open_cases": sum(
            1 for item in serialized_cases
            if is_open_status(item["status"])
        ),
        "overdue_cases": sum(
            1 for item in serialized_cases
            if item["is_overdue"]
        ),
        "cases": serialized_cases,
    }


# --------------------------------------------------
# 8. Duplicate complaint candidates
# --------------------------------------------------


@app.get("/api/duplicates")
def get_duplicates(
    institution_id: str | None = None,
    threshold: float = Query(0.20, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    results = detect_duplicate_candidates(
        db=db,
        institution_id=institution_id,
        threshold=threshold,
    )

    saved_links = db.query(CaseLink).all()

    for item in results:
        # Normalize matching results to the frontend's expected field names.
        item["case_id_1"] = item.get("case_a")
        item["case_id_2"] = item.get("case_b")
        item["description_1"] = item.get("description_a", "")
        item["description_2"] = item.get("description_b", "")

        case_a = item["case_id_1"]
        case_b = item["case_id_2"]

        if case_a is None or case_b is None:
            continue

        pair = {case_a, case_b}

        for link in saved_links:
            saved_pair = {link.source_case_id, link.target_case_id}

            if pair == saved_pair:
                item["relationship_type"] = link.relationship_type
                item["review_status"] = link.review_status
                break

        item.setdefault("relationship_type", "potential_duplicate")
        item.setdefault("review_status", "pending_review")

    return {
        "institution_id": institution_id,
        "threshold": threshold,
        "count": len(results),
        "results": results,
    }

# --------------------------------------------------
# 8.1 Review duplicate complaint candidates
# --------------------------------------------------

@app.post("/api/duplicates/review")
def review_duplicate(
    request: DuplicateReviewRequest,
    db: Session = Depends(get_db),
):
    decision = request.decision.strip().lower()

    if decision not in {"confirm_duplicate", "not_duplicate"}:
        raise HTTPException(
            status_code=400,
            detail=(
                "Decision must be 'confirm_duplicate' "
                "or 'not_duplicate'."
            ),
        )

    if request.case_id_1 == request.case_id_2:
        raise HTTPException(
            status_code=400,
            detail="A case cannot be compared with itself.",
        )

    case_1 = (
        db.query(Case)
        .filter(Case.case_id == request.case_id_1)
        .first()
    )
    case_2 = (
        db.query(Case)
        .filter(Case.case_id == request.case_id_2)
        .first()
    )

    if not case_1 or not case_2:
        raise HTTPException(
            status_code=404,
            detail="One or both cases were not found.",
        )

    if case_1.institution_id != case_2.institution_id:
        raise HTTPException(
            status_code=400,
            detail="Cases must belong to the same institution.",
        )

    link = (
        db.query(CaseLink)
        .filter(
            or_(
                (
                    (CaseLink.source_case_id == case_1.case_id)
                    & (CaseLink.target_case_id == case_2.case_id)
                ),
                (
                    (CaseLink.source_case_id == case_2.case_id)
                    & (CaseLink.target_case_id == case_1.case_id)
                ),
            )
        )
        .first()
    )

    is_duplicate = decision == "confirm_duplicate"

    relationship_type = (
        "duplicate" if is_duplicate else "not_duplicate"
    )
    review_status = (
        "confirmed_duplicate" if is_duplicate else "not_duplicate"
    )

    if link:
        link.relationship_type = relationship_type
        link.review_status = review_status
        if request.similarity_score is not None:
            link.similarity_score = request.similarity_score
    else:
        link = CaseLink(
            source_case_id=case_1.case_id,
            target_case_id=case_2.case_id,
            relationship_type=relationship_type,
            review_status=review_status,
            similarity_score=request.similarity_score,
        )
        db.add(link)

    log_action(
        db=db,
        case_id=case_1.case_id,
        actor_role=request.actor_role,
        action_type=(
            "duplicate_confirmed"
            if is_duplicate
            else "duplicate_rejected"
        ),
        details=(
            f"Reviewer marked {case_1.case_id} and "
            f"{case_2.case_id} as {review_status}."
        ),
    )

    db.commit()
    db.refresh(link)

    return {
        "message": "Duplicate review saved successfully.",
        "case_id_1": case_1.case_id,
        "case_id_2": case_2.case_id,
        "relationship_type": link.relationship_type,
        "review_status": link.review_status,
        "audit_recorded": True,
    }





# --------------------------------------------------
# 9. Cross-bureau advisory alerts
# --------------------------------------------------

@app.get("/api/cases/{case_id}/risk-alerts")
def get_risk_alerts(
    case_id: str,
    db: Session = Depends(get_db),
):
    case = (
        db.query(Case)
        .filter(Case.case_id == case_id)
        .first()
    )

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    category = (case.category or "").strip().lower()

    if category not in APPROVAL_RENEWAL_CATEGORIES:
        return {
            "case_id": case.case_id,
            "institution_id": case.institution_id,
            "alerts_count": 0,
            "alerts": [],
            "message": (
                "Select an approval or renewal case "
                "to view cross-bureau advisory alerts."
            ),
        }

    related_cases = (
        db.query(Case)
        .filter(
            Case.institution_id == case.institution_id,
            Case.case_id != case.case_id,
        )
        .order_by(Case.opened_at.desc())
        .all()
    )

    alerts = []

    for related in related_cases:
        same_bureau = (
            (related.bureau or "").strip().lower()
            == (case.bureau or "").strip().lower()
        )

        if same_bureau or not is_open_status(related.status):
            continue

        alerts.append({
            "related_case_id": related.case_id,
            "bureau": related.bureau,
            "category": related.category,
            "status": related.status,
            "description": related.description,
            "opened_at": to_iso(related.opened_at),
            "due_at": to_iso(related.due_at),
            "alert_type": "cross_bureau_open_case",
            "severity": "advisory",
            "message": (
                f"An open case ({related.case_id}) exists in "
                f"{related.bureau} for the same institution. "
                "Review it before making an approval or renewal "
                "decision."
            ),
        })

    return {
        "case_id": case.case_id,
        "institution_id": case.institution_id,
        "alerts_count": len(alerts),
        "alerts": alerts,
        "decision_impact": (
            "Advisory only. This alert does not block or determine "
            "an approval or renewal decision."
        ),
    }



# --------------------------------------------------
# 10. SLA and overdue cases
# --------------------------------------------------

@app.get("/api/sla/overdue")
def get_overdue_cases(
    bureau: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Case)

    if bureau:
        query = query.filter(
            Case.bureau.ilike(bureau.strip())
        )

    cases = query.order_by(Case.due_at.asc()).all()

    overdue = [
        serialize_case(case)
        for case in cases
        if serialize_case(case)["is_overdue"]
    ]

    return {
        "count": len(overdue),
        "results": overdue,
        "note": "Overdue status is calculated from the case due date.",
    }


# --------------------------------------------------
# 11. Case transfer workflow
# --------------------------------------------------

@app.post("/api/cases/{case_id}/transfer")
def request_case_transfer(
    case_id: str,
    request: TransferRequest,
    db: Session = Depends(get_db),
):
    case = (
        db.query(Case)
        .filter(Case.case_id == case_id)
        .first()
    )

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    target_bureau = request.to_bureau.strip()

    if target_bureau.lower() == case.bureau.strip().lower():
        raise HTTPException(
            status_code=400,
            detail="The target bureau must differ from the current bureau.",
        )

    pending_transfer = (
        db.query(CaseTransfer)
        .filter(
            CaseTransfer.case_id == case_id,
            CaseTransfer.transfer_status == "pending",
        )
        .first()
    )

    if pending_transfer:
        raise HTTPException(
            status_code=409,
            detail="This case already has a pending transfer.",
        )

    transfer = CaseTransfer(
        case_id=case.case_id,
        from_bureau=case.bureau,
        to_bureau=target_bureau,
        reason=request.reason.strip(),
        transfer_status="pending",
        transferred_at=utc_now(),
    )

    db.add(transfer)

    log_action(
        db=db,
        case_id=case.case_id,
        actor_role="Demo Sending Officer",
        action_type="transfer_requested",
        details=(
            f"Transfer requested from {case.bureau} to "
            f"{target_bureau}. Reason: {request.reason.strip()}"
        ),
    )

    db.commit()
    db.refresh(transfer)

    return {
        "message": "Transfer request created.",
        "transfer": serialize_transfer(transfer),
    }


@app.post("/api/transfers/{transfer_id}/acknowledge")
def acknowledge_case_transfer(
    transfer_id: int,
    request: TransferAcknowledgement,
    db: Session = Depends(get_db),
):
    transfer = (
        db.query(CaseTransfer)
        .filter(CaseTransfer.id == transfer_id)
        .first()
    )

    if not transfer:
        raise HTTPException(
            status_code=404,
            detail="Transfer not found",
        )

    if transfer.transfer_status != "pending":
        raise HTTPException(
            status_code=409,
            detail="This transfer is not pending acknowledgement.",
        )

    case = (
        db.query(Case)
        .filter(Case.case_id == transfer.case_id)
        .first()
    )

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Associated case not found",
        )

    transfer.transfer_status = "acknowledged"
    transfer.acknowledged_at = utc_now()

    old_bureau = case.bureau
    case.bureau = transfer.to_bureau

    log_action(
        db=db,
        case_id=case.case_id,
        actor_role=request.actor_role,
        action_type="transfer_acknowledged",
        details=(
            f"Transfer acknowledged. Case bureau updated from "
            f"{old_bureau} to {case.bureau}."
        ),
    )

    db.commit()
    db.refresh(transfer)

    return {
        "message": "Transfer acknowledged and case bureau updated.",
        "transfer": serialize_transfer(transfer),
        "case": serialize_case(case),
    }


# --------------------------------------------------
# 12. Case audit history
# --------------------------------------------------

@app.get("/api/cases/{case_id}/audit")
def get_case_audit(
    case_id: str,
    db: Session = Depends(get_db),
):
    case = (
        db.query(Case)
        .filter(Case.case_id == case_id)
        .first()
    )

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    actions = (
        db.query(CaseAction)
        .filter(CaseAction.case_id == case_id)
        .order_by(CaseAction.created_at.asc())
        .all()
    )

    return {
        "case_id": case_id,
        "count": len(actions),
        "results": [
            {
                "id": action.id,
                "case_id": action.case_id,
                "actor_role": action.actor_role,
                "action_type": action.action_type,
                "details": action.details,
                "created_at": to_iso(action.created_at),
            }
            for action in actions
        ],
    }
