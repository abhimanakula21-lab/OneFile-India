
import re
from rapidfuzz import fuzz

from sqlalchemy.orm import Session
from app.models import Institution, Case

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize_name(name: str) -> str:
    """Normalize names for case-insensitive comparison."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name)

    return name


def resolve_institution(
    db: Session,
    institution_id: str | None = None,
    institution_name: str | None = None,
    region: str | None = None,
):
    """
    Resolve an institution using:
    1. Exact institution ID.
    2. Exact normalized name.
    3. Fuzzy name similarity with supporting region information.

    Fuzzy matches are suggestions, not confirmed identities.
    """

    if institution_id:
        exact_id = (
            db.query(Institution)
            .filter(
                Institution.institution_id == institution_id.strip()
            )
            .first()
        )

        if exact_id:
            return {
                "match_type": "exact_id",
                "confidence": 1.0,
                "confirmed": True,
                "institution": exact_id,
            }

    if not institution_name or not institution_name.strip():
        return {
            "match_type": "no_match",
            "confidence": 0.0,
            "confirmed": False,
            "institution": None,
        }

    target_name = normalize_name(institution_name)
    institutions = db.query(Institution).all()

    # Exact normalized name
    exact_names = [
        inst for inst in institutions
        if normalize_name(inst.name) == target_name
    ]

    # Confirm by name only when it uniquely identifies a record.
    if len(exact_names) == 1:
        return {
            "match_type": "exact_normalized_name",
            "confidence": 1.0,
            "confirmed": False,
            "institution": exact_names[0],
        }

    # Find fuzzy candidates; region is supporting evidence only.
    candidates = []

    for inst in institutions:
        score = fuzz.ratio(
            target_name,
            normalize_name(inst.name)
        ) / 100.0

        region_match = (
            bool(region)
            and bool(inst.region)
            and region.strip().lower() == inst.region.strip().lower()
        )

        candidates.append({
            "institution": inst,
            "name_similarity": round(score, 3),
            "region_match": region_match,
        })

    candidates.sort(
        key=lambda item: (
            item["name_similarity"],
            item["region_match"],
        ),
        reverse=True,
    )

    if not candidates:
        return {
            "match_type": "no_match",
            "confidence": 0.0,
            "confirmed": False,
            "institution": None,
        }

    best = candidates[0]

    # These are demo thresholds. Tune and evaluate them using
    # a labelled synthetic dataset before reporting performance.
    if best["name_similarity"] >= 0.90:
        match_type = "high_similarity_candidate"
    elif best["name_similarity"] >= 0.75:
        match_type = "possible_match"
    else:
        match_type = "no_match"

    return {
        "match_type": match_type,
        "confidence": best["name_similarity"],
        "confirmed": False,
        "institution": (
            best["institution"]
            if match_type != "no_match"
            else None
        ),
        "region_match": best["region_match"],
        "review_required": match_type != "no_match",
    }


def find_related_cases(
    db: Session,
    institution_id: str,
):
    """Retrieve cases belonging to a resolved institution."""
    return (
        db.query(Case)
        .filter(Case.institution_id == institution_id)
        .order_by(Case.opened_at.desc())
        .all()
    )

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def detect_duplicate_candidates(
    db,
    institution_id=None,
    threshold=0.20,
):
    """
    Find potential duplicate cases for the same institution.

    Similarity is a screening signal, not proof of duplication.
    Human review is required.
    """
    query = db.query(Case)

    if institution_id:
        query = query.filter(
            Case.institution_id == institution_id
        )

    cases = query.order_by(Case.opened_at.desc()).all()

    candidates = []

    if len(cases) < 2:
        return candidates

    # Compare cases within the same category.
    groups = {}

    for case in cases:
        category = (case.category or "").strip().lower()
        groups.setdefault(category, []).append(case)

    for category, group in groups.items():
        if len(group) < 2:
            continue

        descriptions = [
            (case.description or "").strip()
            for case in group
        ]

        # Empty descriptions cannot be compared meaningfully.
        valid_indices = [
            i for i, description in enumerate(descriptions)
            if description
        ]

        if len(valid_indices) < 2:
            continue

        valid_descriptions = [
            descriptions[i] for i in valid_indices
        ]

        try:
            vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
            )
            matrix = vectorizer.fit_transform(valid_descriptions)
            similarity_matrix = cosine_similarity(matrix)
        except ValueError:
            # For example, all descriptions may be empty
            # after text preprocessing.
            continue

        for i in range(len(valid_indices)):
            for j in range(i + 1, len(valid_indices)):
                score = float(similarity_matrix[i, j])

                if score < threshold:
                    continue

                case_a = group[valid_indices[i]]
                case_b = group[valid_indices[j]]

                candidates.append({
                    "case_id_1": case_a.case_id,
                    "case_id_2": case_b.case_id,
                    "institution_id": case_a.institution_id,
                    "category": category,
                    "description_1": case_a.description,
                    "description_2": case_b.description,
                    "similarity_score": round(score, 4),
                    "relationship_type": "potential_duplicate",
                    "review_status": "pending_review",
                    "review_required": True,
                })

    candidates.sort(
        key=lambda item: item["similarity_score"],
        reverse=True,
    )

    return candidates


def detect_duplicate_candidates(
    db: Session,
    institution_id: str | None = None,
    threshold: float = 0.20,
):
    """
    Find similar complaint descriptions.

    The threshold is configurable and intended for the demo.
    It must be evaluated against labelled examples before
    being treated as a meaningful operational threshold.
    """

    query = db.query(Case)

    if institution_id:
        query = query.filter(
            Case.institution_id == institution_id
        )

    cases = query.order_by(Case.opened_at.desc()).all()

    candidates = []

    # Compare descriptions only when there are at least two cases.
    for i in range(len(cases)):
        for j in range(i + 1, len(cases)):
            first = cases[i]
            second = cases[j]

            # Avoid comparing records without usable descriptions.
            first_text = (first.description or "").strip()
            second_text = (second.description or "").strip()

            if not first_text or not second_text:
                continue

            # This prototype compares cases from the same institution.
            if first.institution_id != second.institution_id:
                continue

            # Different topics should not be flagged solely because
            # the institution is the same.
            if (
                first.category
                and second.category
                and first.category.lower() != second.category.lower()
            ):
                continue

            vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
            )

            try:
                vectors = vectorizer.fit_transform(
                    [first_text, second_text]
                )
                score = float(
                    cosine_similarity(vectors[0], vectors[1])[0][0]
                )
            except ValueError:
                continue

            if score >= threshold:
                candidates.append({
                    "institution_id": first.institution_id,
                    "case_a": first.case_id,
                    "case_b": second.case_id,
                    "description_a": first_text,
                    "description_b": second_text,
                    "similarity_score": round(score, 3),
                    "review_status": "pending_review",
                })

    return candidates


