"""Schema contract tests for candidate intelligence persistence."""

from app.models import CandidateEvidence, CandidateSkillProfile, KnowledgeConcept
from app.models.intelligence import ProjectKnowledgeConcept, SessionTranscriptSegment


def test_candidate_intelligence_models_register_with_metadata() -> None:
    expected_tables = {
        "knowledge_concepts",
        "project_knowledge_concepts",
        "candidate_skill_profiles",
        "session_transcript_segments",
        "candidate_evidence",
    }

    assert expected_tables.issubset(set(KnowledgeConcept.metadata.tables))
    assert CandidateSkillProfile.__tablename__ == "candidate_skill_profiles"
    assert CandidateEvidence.__tablename__ == "candidate_evidence"
    assert ProjectKnowledgeConcept.__tablename__ == "project_knowledge_concepts"
    assert SessionTranscriptSegment.__tablename__ == "session_transcript_segments"


def test_skill_profile_does_not_default_to_a_fabricated_score() -> None:
    columns = CandidateSkillProfile.__table__.c

    assert columns.proficiency.nullable is True
    assert columns.confidence.nullable is True
    assert columns.evidence_count.default.arg == 0
    assert columns.assessment_status.default.arg == "unassessed"


def test_transcript_has_idempotency_and_ordering_constraints() -> None:
    constraints = SessionTranscriptSegment.__table__.constraints
    unique_constraints = {
        tuple(column.name for column in constraint.columns)
        for constraint in constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert ("session_id", "sequence_number") in unique_constraints
    assert "speaker" in SessionTranscriptSegment.__table__.c
    assert "elapsed_ms" in SessionTranscriptSegment.__table__.c
