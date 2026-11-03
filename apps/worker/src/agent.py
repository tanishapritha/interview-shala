"""LiveKit voice interviewer entrypoint and trusted transcript ingestion."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from uuid import UUID

from livekit import agents
from livekit.agents import (
    Agent,
    AgentSession,
    ConversationItemAddedEvent,
    UserInputTranscribedEvent,
)
from livekit.plugins import cartesia, deepgram, openai, silero

from src.api_client import InterviewShalaAPI
from src.settings import get_settings

logger = logging.getLogger("interview_shala.worker")
ROOM_PATTERN = re.compile(r"^interview-shala-([0-9a-fA-F-]{36})$")


def session_id_from_room(room_name: str) -> UUID:
    match = ROOM_PATTERN.fullmatch(room_name)
    if match is None:
        raise ValueError("Room name is not a valid Interview Shala practice session")
    return UUID(match.group(1))


def build_instructions(context: dict) -> str:
    company = context["company"]
    role = context["role"]
    round_type = str(context["round_type"]).replace("_", " ")
    job_description = context.get("job_description") or "Not provided."

    return f"""
You are Interview Shala, a rigorous but fair human-like interviewer.
Conduct a {round_type} interview for the {role} role at {company}.

Role context:
{job_description}

Interview rules:
- Ask one question at a time and wait for the candidate's complete answer.
- Probe reasoning, assumptions, trade-offs, and practical experience.
- Do not reveal a model answer before the candidate has attempted the question.
- Ask concise, natural follow-ups; avoid long lectures.
- Do not claim to evaluate or score the candidate during the live conversation.
- If the candidate asks for clarification, clarify the question without giving away its answer.
- Keep the interview professional, respectful, and realistic.
- Start by briefly introducing yourself and asking the candidate to introduce themselves.
""".strip()


async def entrypoint(ctx: agents.JobContext) -> None:
    settings = get_settings()
    session_id = session_id_from_room(ctx.room.name)
    api = InterviewShalaAPI(
        settings.interview_shala_api_url,
        settings.worker_shared_secret,
        settings.request_timeout_seconds,
    )

    try:
        context = await api.get_session(session_id)
        next_sequence = int(context["next_sequence"])
        started_at = time.monotonic()
        sequence_lock = asyncio.Lock()
        pending_writes: set[asyncio.Task[None]] = set()

        async def persist(speaker: str, text: str) -> None:
            nonlocal next_sequence
            normalized = text.strip()
            if not normalized:
                return
            async with sequence_lock:
                sequence = next_sequence
                next_sequence += 1
                elapsed_ms = max(0, int((time.monotonic() - started_at) * 1000))
                await api.append_transcript(
                    session_id,
                    sequence_number=sequence,
                    speaker=speaker,
                    text=normalized,
                    elapsed_ms=elapsed_ms,
                )

        session = AgentSession(
            stt=deepgram.STT(
                model=settings.deepgram_model,
                language=settings.stt_language,
            ),
            llm=openai.LLM(
                model=settings.openrouter_model,
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.openrouter_api_key,
            ),
            tts=cartesia.TTS(
                model="sonic-3",
                voice=settings.cartesia_voice_id,
            ),
            vad=silero.VAD.load(),
        )

        async def persist_safely(speaker: str, text: str) -> None:
            try:
                await persist(speaker, text)
            except Exception:
                logger.exception(
                    "Transcript persistence failed",
                    extra={"session_id": str(session_id), "speaker": speaker},
                )

        def schedule_persist(speaker: str, text: str) -> None:
            task = asyncio.create_task(persist_safely(speaker, text))
            pending_writes.add(task)
            task.add_done_callback(pending_writes.discard)

        @session.on("user_input_transcribed")
        def on_user_input_transcribed(event: UserInputTranscribedEvent) -> None:
            if event.is_final:
                schedule_persist("candidate", event.transcript)

        @session.on("conversation_item_added")
        def on_conversation_item_added(event: ConversationItemAddedEvent) -> None:
            item = event.item
            if item.role == "assistant" and not item.interrupted:
                text = item.text_content
                if text:
                    schedule_persist("interviewer", text)

        @session.on("error")
        def on_session_error(event) -> None:
            logger.error(
                "LiveKit session model error",
                extra={
                    "session_id": str(session_id),
                    "recoverable": event.error.recoverable,
                    "source": type(event.source).__name__,
                },
            )

        ctx.log_context_fields = {
            "interview_session_id": str(session_id),
            "project_id": context["project_id"],
        }

        await session.start(
            room=ctx.room,
            agent=Agent(instructions=build_instructions(context)),
        )
        await session.generate_reply(
            instructions=(
                "Greet the candidate, explain that this is a practice interview, "
                "and ask them to introduce themselves."
            )
        )
    finally:
        if "pending_writes" in locals() and pending_writes:
            await asyncio.gather(*pending_writes, return_exceptions=True)
        await api.aclose()


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
