"""
Gemini Live voice session proxy helpers.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import Iterable
from typing import Any

from fastapi import WebSocket
from google import genai
from google.genai import types

from config import Config, Prompts

logger = logging.getLogger(__name__)

PCM_INPUT_MIME = "audio/pcm;rate=16000"

# English command words
COMMAND_WORDS_EN = {
    "play",
    "pause",
    "next",
    "previous",
    "bookmark",
    "rewind",
    "forward",
}

# Chinese command words mapped to English equivalents
COMMAND_WORDS_ZH = {
    "播放": "play",
    "开始": "play",
    "暂停": "pause",
    "停止": "pause",
    "下一个": "next",
    "下一条": "next",
    "上一个": "previous",
    "上一条": "previous",
    "收藏": "bookmark",
    "书签": "bookmark",
    "后退": "rewind",
    "倒退": "rewind",
    "快进": "forward",
    "前进": "forward",
}

# Combined for quick lookup
COMMAND_WORDS = COMMAND_WORDS_EN | set(COMMAND_WORDS_ZH.keys())

COMMAND_NOUNS = {"segment", "story", "one", "item"}
FILLER_WORDS_EN = {
    "please",
    "now",
    "thanks",
    "thank",
    "you",
    "can",
    "could",
    "would",
    "me",
    "the",
    "a",
    "an",
    "to",
}
# Chinese filler words that appear BEFORE commands
FILLER_WORDS_ZH_PREFIX = {
    "请",
    "帮我",
    "帮",
    "我",
}
# Chinese particles that appear AFTER commands
FILLER_WORDS_ZH_SUFFIX = {
    "一下",
    "吧",
    "啊",
    "呢",
    "了",
}
FILLER_WORDS_ZH = FILLER_WORDS_ZH_PREFIX | FILLER_WORDS_ZH_SUFFIX
FILLER_WORDS = FILLER_WORDS_EN | FILLER_WORDS_ZH


def _normalize_command_text(text: str) -> list[str]:
    """Normalize text for command detection, supporting both English and Chinese."""
    # Convert to lowercase for English words
    text_lower = text.lower()
    # Remove punctuation but keep Chinese characters and alphanumeric
    cleaned = re.sub(r"[^\w\u4e00-\u9fff\s]", " ", text_lower)

    # For Chinese text, remove prefix filler words from the beginning
    for filler in sorted(FILLER_WORDS_ZH_PREFIX, key=len, reverse=True):
        if cleaned.startswith(filler):
            cleaned = cleaned[len(filler):]
            break

    # Remove suffix filler words from the end
    for filler in sorted(FILLER_WORDS_ZH_SUFFIX, key=len, reverse=True):
        if cleaned.endswith(filler):
            cleaned = cleaned[:-len(filler)]
            break

    tokens = [token for token in cleaned.split() if token]
    # Remove leading English filler words
    while tokens and tokens[0] in FILLER_WORDS_EN:
        tokens.pop(0)
    return tokens


def _detect_command(text: str) -> tuple[str | None, dict[str, Any]]:
    tokens = _normalize_command_text(text)
    if not tokens:
        return None, {}

    first_token = tokens[0]

    # Check if it's a recognized command
    if first_token not in COMMAND_WORDS:
        return None, {}

    # Normalize Chinese commands to English equivalents
    if first_token in COMMAND_WORDS_ZH:
        command = COMMAND_WORDS_ZH[first_token]
    else:
        command = first_token

    rest = tokens[1:]
    if not rest:
        return command, {}

    if command in {"next", "previous"} and all(
        word in COMMAND_NOUNS or word in FILLER_WORDS for word in rest
    ):
        return command, {}

    if command in {"play", "pause", "bookmark"} and all(
        word in FILLER_WORDS for word in rest
    ):
        return command, {}

    if command in {"rewind", "forward"}:
        for word in rest:
            if word.isdigit():
                return command, {"seconds": float(word)}
        if all(word in FILLER_WORDS for word in rest):
            return command, {}

    return None, {}


def build_system_prompt(context: str, language: str = "en") -> str:
    """Create the system prompt with newsletter context and tool guidance."""
    # Use language-specific prompt for voice mode
    template = Prompts.get_voice_mode_prompt(language).strip()
    if template:
        if "{context}" in template:
            return template.replace("{context}", context)
        return f"{template}\n\n<newsletter>\n{context}\n</newsletter>"

    return (
        "You are a voice assistant for a newsletter audio player. "
        "You can control playback with tool calls and answer questions "
        "about the newsletter content.\n\n"
        "If the user says a command like play, pause, next, previous, "
        "bookmark, rewind, or forward, call the matching tool. "
        "Do not speak a confirmation for commands. "
        "If the user asks a question, answer using ONLY the content below. "
        "If the answer is not in the content, say so politely.\n\n"
        "<newsletter>\n"
        f"{context}\n"
        "</newsletter>"
    )


def build_tools() -> list[dict[str, Any]]:
    """Define tool declarations for voice commands."""
    return [
        {
            "function_declarations": [
                {
                    "name": "next",
                    "description": "Advance to the next segment.",
                },
                {
                    "name": "play",
                    "description": "Resume newsletter playback.",
                },
                {
                    "name": "pause",
                    "description": "Pause newsletter playback.",
                },
                {
                    "name": "previous",
                    "description": "Go back to the previous segment.",
                },
                {
                    "name": "bookmark",
                    "description": "Bookmark the current segment.",
                },
                {
                    "name": "rewind",
                    "description": "Rewind the current audio by a few seconds.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "seconds": {
                                "type": "number",
                                "description": "Seconds to rewind (default 5).",
                            }
                        },
                    },
                },
                {
                    "name": "forward",
                    "description": "Skip forward by a few seconds.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "seconds": {
                                "type": "number",
                                "description": "Seconds to skip (default 5).",
                            }
                        },
                    },
                },
            ]
        }
    ]


class VoiceSession:
    """Manage a single Gemini Live session for one client WebSocket."""

    def __init__(self, issue_id: str, context: str, resume_handle: str | None = None, language: str = "en"):
        self.issue_id = issue_id
        self.context = context
        self.language = language
        self._resume_handle = resume_handle
        self._client = genai.Client(
            vertexai=True,
            project=Config.GCP_PROJECT_ID,
            location=Config.VOICE_MODE_REGION,
        )
        self._session: Any | None = None
        self._session_cm: Any | None = None
        self._session_lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
        self._audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=80)
        self._last_drop_log = 0.0
        self._suppress_output = False
        self._last_command_text: str | None = None
        self._last_command_time = 0.0

    async def _open_session(self) -> Any:
        config_kwargs: dict[str, Any] = {
            "response_modalities": ["AUDIO"],
            "system_instruction": build_system_prompt(self.context, self.language),
            "tools": build_tools(),
            "input_audio_transcription": {},
            "output_audio_transcription": {},
        }
        if self._resume_handle:
            config_kwargs["session_resumption"] = types.SessionResumptionConfig(
                handle=self._resume_handle
            )

        config = types.LiveConnectConfig(**config_kwargs)
        self._session_cm = self._client.aio.live.connect(
            model=Config.VOICE_MODE_MODEL,
            config=config,
        )
        self._session = await self._session_cm.__aenter__()
        logger.info("Gemini Live session started for issue %s", self.issue_id)
        return self._session

    async def _ensure_session(self) -> Any:
        async with self._session_lock:
            if self._session is None:
                await self._open_session()
            return self._session

    async def _close_session(self) -> None:
        if self._session_cm is not None:
            await self._session_cm.__aexit__(None, None, None)
        self._session = None
        self._session_cm = None

    async def _reset_session(self) -> None:
        await self._close_session()

    async def _send_tool_ack(self, tool_call: Any) -> None:
        session = await self._ensure_session()
        try:
            response_payload = {
                "name": tool_call.name,
                "response": {"output": "ok"},
            }
            if getattr(tool_call, "id", None):
                response_payload["id"] = tool_call.id
            function_response = types.FunctionResponse(**response_payload)
            await session.send_tool_response(function_responses=function_response)
        except Exception:
            logger.exception("Failed to send tool response ack")

    async def _emit_tool_call(
        self, websocket: WebSocket, name: str, args: dict[str, Any] | None = None
    ) -> None:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "tool_call",
                    "name": name,
                    "args": args or {},
                }
            )
        )

    async def _forward_gemini(self, websocket: WebSocket) -> None:
        while not self._stop_event.is_set():
            session = await self._ensure_session()
            try:
                async for message in session.receive():
                    await self._handle_server_message(message, websocket)
            except Exception:
                logger.warning("Gemini Live receive loop failed, reconnecting", exc_info=True)
                await self._reset_session()
                await asyncio.sleep(0.5)

    async def _forward_client_audio(self) -> None:
        while not self._stop_event.is_set():
            chunk = await self._audio_queue.get()
            if chunk is None:
                break
            await self._send_audio_chunk(chunk)

    async def _send_audio_chunk(self, chunk: bytes) -> None:
        for attempt in range(2):
            try:
                session = await self._ensure_session()
                await session.send_realtime_input(
                    audio=types.Blob(data=chunk, mime_type=PCM_INPUT_MIME)
                )
                return
            except Exception:
                logger.warning("Audio send failed (attempt %s)", attempt + 1, exc_info=True)
                await self._reset_session()
                await asyncio.sleep(0.2)

    async def _handle_server_message(self, message: Any, websocket: WebSocket) -> None:
        if getattr(message, "session_resumption_update", None):
            update = message.session_resumption_update
            new_handle = getattr(update, "new_handle", None)
            resumable = getattr(update, "resumable", None)
            if new_handle:
                self._resume_handle = new_handle
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "session_resumption",
                            "handle": new_handle,
                            "resumable": bool(resumable),
                        }
                    )
                )

        if getattr(message, "go_away", None):
            go_away = message.go_away
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "go_away",
                        "timeLeftMs": getattr(go_away, "time_left", None),
                    }
                )
            )

        if getattr(message, "tool_call", None):
            tool_call = message.tool_call
            function_calls: Iterable[Any] = getattr(tool_call, "function_calls", []) or []
            for call in function_calls:
                now = asyncio.get_running_loop().time()
                if (
                    call.name == self._last_command_text
                    and now - self._last_command_time < 1.0
                ):
                    await self._send_tool_ack(call)
                    continue
                self._last_command_text = call.name
                self._last_command_time = now
                self._suppress_output = True
                await self._emit_tool_call(
                    websocket, call.name, getattr(call, "args", {}) or {}
                )
                await self._send_tool_ack(call)

        server_content = getattr(message, "server_content", None)
        if server_content:
            input_transcription = getattr(server_content, "input_transcription", None)
            if input_transcription and getattr(input_transcription, "text", None):
                finished = getattr(input_transcription, "finished", None)
                if finished is not False:
                    command, args = _detect_command(input_transcription.text)
                    if command:
                        now = asyncio.get_running_loop().time()
                        if (
                            command != self._last_command_text
                            or now - self._last_command_time > 1.0
                        ):
                            self._last_command_text = command
                            self._last_command_time = now
                            self._suppress_output = True
                            await self._emit_tool_call(websocket, command, args)

            output_transcription = getattr(server_content, "output_transcription", None)
            if (
                not self._suppress_output
                and output_transcription
                and getattr(output_transcription, "text", None)
            ):
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "transcript",
                            "text": output_transcription.text,
                        }
                    )
                )
            if self._suppress_output and (
                getattr(server_content, "turn_complete", False)
                or getattr(server_content, "generation_complete", False)
                or getattr(server_content, "waiting_for_input", False)
            ):
                self._suppress_output = False

        if not self._suppress_output and getattr(message, "data", None):
            await websocket.send_bytes(message.data)
        elif (
            not self._suppress_output
            and server_content
            and getattr(server_content, "model_turn", None)
        ):
            parts = getattr(server_content.model_turn, "parts", []) or []
            for part in parts:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    await websocket.send_bytes(inline_data.data)

        if not self._suppress_output and getattr(message, "text", None):
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "text",
                        "text": message.text,
                    }
                )
            )

    async def enqueue_audio(self, chunk: bytes) -> None:
        try:
            self._audio_queue.put_nowait(chunk)
        except asyncio.QueueFull:
            try:
                self._audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                self._audio_queue.put_nowait(chunk)
            except asyncio.QueueFull:
                pass
            now = asyncio.get_running_loop().time()
            if now - self._last_drop_log > 2:
                self._last_drop_log = now
                logger.warning("Dropping audio chunk due to backpressure")

    async def listen_to_client(self, websocket: WebSocket) -> None:
        try:
            while True:
                message = await websocket.receive()
                if message.get("bytes") is not None:
                    await self.enqueue_audio(message["bytes"])
                elif message.get("text") is not None:
                    await self.handle_client_text(message["text"], websocket)
        except Exception:
            logger.info("Client WebSocket disconnected for issue %s", self.issue_id)
            self._stop_event.set()
            await self._audio_queue.put(None)
            await self._reset_session()

    async def handle_client_text(self, payload: str, websocket: WebSocket) -> None:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return

        message_type = data.get("type")
        if message_type == "start" and data.get("resumeHandle"):
            self._resume_handle = data["resumeHandle"]
            await websocket.send_text(json.dumps({"type": "start_ack"}))
        elif message_type == "resume" and data.get("handle"):
            self._resume_handle = data["handle"]
            await websocket.send_text(json.dumps({"type": "resume_ack"}))

    async def run(self, websocket: WebSocket) -> None:
        receiver_task = asyncio.create_task(self._forward_gemini(websocket))
        sender_task = asyncio.create_task(self._forward_client_audio())

        done, pending = await asyncio.wait(
            [receiver_task, sender_task], return_when=asyncio.FIRST_EXCEPTION
        )

        for task in pending:
            task.cancel()

        self._stop_event.set()
        await self._close_session()
        for task in done:
            if task.exception():
                logger.error("Voice session task error: %s", task.exception())
