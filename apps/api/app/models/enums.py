"""Shared domain enumerations."""

from enum import StrEnum


class RoundType(StrEnum):
    TECHNICAL = "technical"
    HR = "hr"
    BEHAVIORAL = "behavioral"
    PROJECT = "project"
    SYSTEM_DESIGN = "system_design"
    DSA = "dsa"


class SessionStatus(StrEnum):
    PENDING = "pending"
    CONNECTING = "connecting"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    RECONNECTING = "reconnecting"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(StrEnum):
    MILD = "mild"
    MODERATE = "moderate"
    NEEDS_IMPROVEMENT = "needs_improvement"
    CRITICAL = "critical"
