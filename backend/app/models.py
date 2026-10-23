
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    region = Column(String(100))
    address = Column(String(300))

    cases = relationship("Case", back_populates="institution")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, index=True, nullable=False)

    institution_id = Column(
        String(50),
        ForeignKey("institutions.institution_id"),
        index=True,
        nullable=False,
    )

    bureau = Column(String(100), nullable=False)
    category = Column(String(100))
    source = Column(String(150))
    description = Column(Text)
    status = Column(String(50), nullable=False, default="Pending")

    opened_at = Column(Date, nullable=False)
    due_at = Column(Date)

    created_at = Column(DateTime(timezone=True), default=utc_now)

    institution = relationship("Institution", back_populates="cases")


class CaseLink(Base):
    __tablename__ = "case_links"

    id = Column(Integer, primary_key=True, index=True)
    source_case_id = Column(
        String(50), ForeignKey("cases.case_id"), nullable=False
    )
    target_case_id = Column(
        String(50), ForeignKey("cases.case_id"), nullable=False
    )
    relationship_type = Column(String(50), default="potential_duplicate")
    review_status = Column(String(30), default="pending_review")
    similarity_score = Column(Float)


class CaseTransfer(Base):
    __tablename__ = "case_transfers"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("cases.case_id"), nullable=False)
    from_bureau = Column(String(100), nullable=False)
    to_bureau = Column(String(100), nullable=False)
    reason = Column(Text)
    transfer_status = Column(String(30), default="pending")
    transferred_at = Column(DateTime(timezone=True), default=utc_now)
    acknowledged_at = Column(DateTime(timezone=True))


class CaseAction(Base):
    __tablename__ = "case_actions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), ForeignKey("cases.case_id"), nullable=False)
    actor_role = Column(String(100))
    action_type = Column(String(100), nullable=False)
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    role = Column(String(50), nullable=False)
    bureau = Column(String(100))
