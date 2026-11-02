"""Rule-based preparation plan generator with optional LLM enhancement."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.models.enums import RoundType

logger = logging.getLogger(__name__)


@dataclass
class PlannedTask:
    title: str
    description: str | None
    round_type: RoundType
    priority: int
    estimated_minutes: int
    is_today: bool = False
    due_date_offset_days: int = 0


@dataclass
class PlannedRound:
    name: str
    round_type: RoundType
    priority: int
    topics: list[str]
    question_count: int
    description: str | None = None


@dataclass
class PlannedPreparation:
    summary: str
    rounds: list[PlannedRound] = field(default_factory=list)
    tasks: list[PlannedTask] = field(default_factory=list)
    source: str = "template"


ROLE_TOPIC_HINTS: dict[str, list[str]] = {
    "frontend": ["JavaScript/TypeScript", "React", "CSS/Accessibility", "Web Performance", "Testing"],
    "backend": ["API Design", "Databases", "Caching", "Concurrency", "Observability"],
    "fullstack": ["System Design Basics", "APIs", "Frontend Architecture", "Databases", "DevOps Basics"],
    "mobile": ["Platform APIs", "State Management", "Offline Sync", "Performance", "App Store Guidelines"],
    "data": ["SQL", "ETL Pipelines", "Statistics", "ML Fundamentals", "Data Modeling"],
    "ml": ["ML Fundamentals", "Feature Engineering", "Model Evaluation", "MLOps", "Deep Learning"],
    "devops": ["CI/CD", "Kubernetes", "Infrastructure as Code", "Observability", "Security"],
    "sre": ["SLIs/SLOs", "Incident Response", "Capacity Planning", "Reliability Patterns", "Observability"],
    "product": ["Product Sense", "Metrics", "Stakeholder Communication", "Prioritization", "User Research"],
    "default": ["Core Fundamentals", "Problem Solving", "System Thinking", "Communication", "Domain Knowledge"],
}


ROUND_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "Technical Round",
        "round_type": RoundType.TECHNICAL,
        "priority": 1,
        "question_count": 8,
        "description": "Core technical depth for the target role.",
        "base_topics": True,
    },
    {
        "name": "DSA / Problem Solving",
        "round_type": RoundType.DSA,
        "priority": 2,
        "question_count": 6,
        "description": "Algorithms, data structures, and coding fluency.",
        "topics": ["Arrays & Strings", "Trees & Graphs", "Dynamic Programming", "Complexity Analysis"],
    },
    {
        "name": "System Design",
        "round_type": RoundType.SYSTEM_DESIGN,
        "priority": 3,
        "question_count": 4,
        "description": "Architecture trade-offs, scalability, and reliability.",
        "topics": ["Requirements Clarification", "High-Level Design", "Data Modeling", "Trade-offs"],
    },
    {
        "name": "Project Deep Dive",
        "round_type": RoundType.PROJECT,
        "priority": 4,
        "question_count": 5,
        "description": "Walk through past projects with ownership and impact.",
        "topics": ["Architecture Decisions", "Challenges Faced", "Metrics & Impact", "Collaboration"],
    },
    {
        "name": "Behavioral Round",
        "round_type": RoundType.BEHAVIORAL,
        "priority": 5,
        "question_count": 6,
        "description": "STAR stories for leadership, conflict, and ownership.",
        "topics": ["Leadership", "Conflict Resolution", "Failure & Learning", "Collaboration"],
    },
    {
        "name": "HR / Culture Fit",
        "round_type": RoundType.HR,
        "priority": 6,
        "question_count": 5,
        "description": "Motivation, compensation expectations, and company fit.",
        "topics": ["Motivation", "Career Goals", "Company Research", "Logistics"],
    },
]


def _infer_role_bucket(role: str) -> str:
    lowered = role.lower()
    mapping = [
        (("frontend", "front-end", "react", "ui engineer", "web engineer"), "frontend"),
        (("backend", "back-end", "server", "api engineer"), "backend"),
        (("full stack", "fullstack", "full-stack"), "fullstack"),
        (("mobile", "android", "ios", "flutter", "react native"), "mobile"),
        (("data engineer", "analytics engineer", "data analyst"), "data"),
        (("machine learning", "ml engineer", "ai engineer", "data scientist"), "ml"),
        (("devops", "platform engineer", "infrastructure"), "devops"),
        (("sre", "reliability"), "sre"),
        (("product manager", "product owner", "pm "), "product"),
    ]
    for keywords, bucket in mapping:
        if any(k in lowered for k in keywords):
            return bucket
    return "default"


def _days_until(interview_date: date | None) -> int | None:
    if interview_date is None:
        return None
    today = datetime.now(timezone.utc).date()
    return max((interview_date - today).days, 0)


def build_template_plan(
    *,
    company: str,
    role: str,
    job_description: str | None = None,
    interview_date: date | None = None,
    additional_context: str | None = None,
) -> PlannedPreparation:
    """Solid rule-based planner used when no LLM is configured."""
    bucket = _infer_role_bucket(role)
    topics = list(ROLE_TOPIC_HINTS.get(bucket, ROLE_TOPIC_HINTS["default"]))
    days_left = _days_until(interview_date)

    if job_description:
        # Light keyword boost from JD without calling an LLM
        jd_lower = job_description.lower()
        extras = []
        for keyword, label in [
            ("kubernetes", "Kubernetes"),
            ("aws", "AWS"),
            ("gcp", "GCP"),
            ("azure", "Azure"),
            ("graphql", "GraphQL"),
            ("kafka", "Kafka"),
            ("spark", "Spark"),
            ("python", "Python"),
            ("java", "Java"),
            ("golang", "Go"),
            ("typescript", "TypeScript"),
            ("security", "Security"),
        ]:
            if keyword in jd_lower and label not in topics:
                extras.append(label)
        topics = (extras + topics)[:8]

    rounds: list[PlannedRound] = []
    for tmpl in ROUND_TEMPLATES:
        round_topics = list(tmpl.get("topics") or [])
        if tmpl.get("base_topics"):
            round_topics = topics[:5]
        rounds.append(
            PlannedRound(
                name=tmpl["name"],
                round_type=tmpl["round_type"],
                priority=tmpl["priority"],
                topics=round_topics,
                question_count=tmpl["question_count"],
                description=tmpl.get("description"),
            )
        )

    horizon = days_left if days_left is not None else 14
    intensity = "intensive" if horizon <= 7 else "steady" if horizon <= 21 else "foundational"

    summary_parts = [
        f"Preparation plan for {role} at {company}.",
        f"Focus track: {bucket.replace('_', ' ')}.",
        f"Recommended pace: {intensity} over ~{horizon} day(s).",
    ]
    if additional_context:
        summary_parts.append("Custom context noted and reflected in today's tasks.")
    summary = " ".join(summary_parts)

    tasks: list[PlannedTask] = [
        PlannedTask(
            title=f"Research {company}'s product, culture, and recent news",
            description="Prepare 3 talking points tying your experience to the company.",
            round_type=RoundType.HR,
            priority=1,
            estimated_minutes=30,
            is_today=True,
            due_date_offset_days=0,
        ),
        PlannedTask(
            title=f"Map JD requirements to your experience for {role}",
            description="List must-have skills and rate yourself; note gaps for practice.",
            round_type=RoundType.TECHNICAL,
            priority=2,
            estimated_minutes=25,
            is_today=True,
            due_date_offset_days=0,
        ),
        PlannedTask(
            title="Complete one timed DSA warm-up set",
            description="2 easy + 1 medium problems; narrate your approach out loud.",
            round_type=RoundType.DSA,
            priority=3,
            estimated_minutes=45,
            is_today=True,
            due_date_offset_days=0,
        ),
        PlannedTask(
            title="Draft 3 STAR stories for behavioral questions",
            description="Cover conflict, failure, and leadership with measurable outcomes.",
            round_type=RoundType.BEHAVIORAL,
            priority=4,
            estimated_minutes=35,
            is_today=False,
            due_date_offset_days=1,
        ),
        PlannedTask(
            title="Prepare a 5-minute project deep-dive narrative",
            description="Problem → approach → trade-offs → impact for your strongest project.",
            round_type=RoundType.PROJECT,
            priority=5,
            estimated_minutes=30,
            is_today=False,
            due_date_offset_days=1,
        ),
        PlannedTask(
            title="Sketch a high-level system design for a familiar product",
            description="Include API, storage, bottlenecks, and one scaling lever.",
            round_type=RoundType.SYSTEM_DESIGN,
            priority=6,
            estimated_minutes=40,
            is_today=False,
            due_date_offset_days=2,
        ),
        PlannedTask(
            title=f"Mock technical voice session focused on {topics[0] if topics else 'core skills'}",
            description="Practice answering out loud; record and note filler words.",
            round_type=RoundType.TECHNICAL,
            priority=7,
            estimated_minutes=40,
            is_today=False,
            due_date_offset_days=2,
        ),
        PlannedTask(
            title="HR Q&A rehearsal (motivation, notice period, expectations)",
            description="Keep answers concise and aligned with the role.",
            round_type=RoundType.HR,
            priority=8,
            estimated_minutes=20,
            is_today=False,
            due_date_offset_days=3,
        ),
    ]

    if intensity == "intensive":
        for task in tasks:
            if task.due_date_offset_days <= 1:
                task.is_today = True

    return PlannedPreparation(summary=summary, rounds=rounds, tasks=tasks, source="template")


async def _call_llm(prompt: str, settings: Settings) -> dict[str, Any] | None:
    """Call Groq or OpenRouter; return parsed JSON or None on failure."""
    try:
        # Prefer shared prompts package when available on PYTHONPATH / monorepo.
        from interview_prompts import PLANNER_SYSTEM_PROMPT as system  # type: ignore
    except ImportError:
        system = (
            "You are an expert interview coach. Return ONLY valid JSON with keys: "
            "summary (string), rounds (array of {name, round_type, priority, topics, "
            "question_count, description}), tasks (array of {title, description, round_type, "
            "priority, estimated_minutes, is_today, due_date_offset_days}). "
            "round_type must be one of: technical, hr, behavioral, project, system_design, dsa."
        )

    if settings.groq_api_key:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": settings.llm_model,
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
    elif settings.openrouter_api_key:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/tanishapritha/interview-shala",
            "X-Title": "Interview Shala",
        }
        body = {
            "model": settings.openrouter_model,
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
    else:
        return None

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(url, headers=headers, json=body)
            if response.status_code >= 400:
                logger.warning("LLM planner request failed: %s %s", response.status_code, response.text[:300])
                return None
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception:  # noqa: BLE001
        logger.exception("LLM planner enhancement failed; falling back to template")
        return None


def _parse_llm_plan(data: dict[str, Any], fallback: PlannedPreparation) -> PlannedPreparation:
    try:
        rounds: list[PlannedRound] = []
        for item in data.get("rounds") or []:
            rt = RoundType(str(item.get("round_type", RoundType.TECHNICAL)))
            rounds.append(
                PlannedRound(
                    name=str(item.get("name") or rt.value.title()),
                    round_type=rt,
                    priority=int(item.get("priority") or 1),
                    topics=[str(t) for t in (item.get("topics") or [])],
                    question_count=int(item.get("question_count") or 5),
                    description=item.get("description"),
                )
            )
        tasks: list[PlannedTask] = []
        for item in data.get("tasks") or []:
            rt = RoundType(str(item.get("round_type", RoundType.TECHNICAL)))
            tasks.append(
                PlannedTask(
                    title=str(item.get("title") or "Practice task"),
                    description=item.get("description"),
                    round_type=rt,
                    priority=int(item.get("priority") or 1),
                    estimated_minutes=int(item.get("estimated_minutes") or 30),
                    is_today=bool(item.get("is_today", False)),
                    due_date_offset_days=int(item.get("due_date_offset_days") or 0),
                )
            )
        if not rounds or not tasks:
            return fallback
        return PlannedPreparation(
            summary=str(data.get("summary") or fallback.summary),
            rounds=rounds,
            tasks=tasks,
            source="llm",
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to parse LLM plan JSON")
        return fallback


async def generate_preparation_plan(
    *,
    company: str,
    role: str,
    job_description: str | None = None,
    interview_date: date | None = None,
    company_url: str | None = None,
    additional_context: str | None = None,
    settings: Settings | None = None,
) -> PlannedPreparation:
    """Generate a plan via template, optionally enhanced by LLM when keys are set."""
    cfg = settings or get_settings()
    template = build_template_plan(
        company=company,
        role=role,
        job_description=job_description,
        interview_date=interview_date,
        additional_context=additional_context,
    )

    if not cfg.llm_configured:
        return template

    prompt = (
        f"Create an interview preparation plan.\n"
        f"Company: {company}\n"
        f"Role: {role}\n"
        f"Interview date: {interview_date or 'unknown'}\n"
        f"Company URL: {company_url or 'n/a'}\n"
        f"Job description:\n{job_description or 'n/a'}\n"
        f"Additional context:\n{additional_context or 'n/a'}\n"
        f"Include rounds: technical, dsa, system_design, project, behavioral, hr.\n"
        f"Include at least 3 tasks marked is_today=true for today."
    )
    llm_data = await _call_llm(prompt, cfg)
    if not llm_data:
        return template
    return _parse_llm_plan(llm_data, template)
