
"""Temporary, anonymous analysis sessions."""

import hashlib
import hmac
import secrets
import threading
import time

from contextlib import contextmanager
from dataclasses import dataclass, field
from uuid import uuid4

from fastapi import HTTPException


SESSION_TTL_SECONDS = 15 * 60


@dataclass
class AnalysisSession:
    token_hash: bytes
    expires_at: float
    lock: threading.Lock = field(
        default_factory=threading.Lock
    )


class SessionStore:

    def __init__(self, checkpointer, ttl=SESSION_TTL_SECONDS):
        self.checkpointer = checkpointer
        self.ttl = ttl
        self.sessions = {}
        self.lock = threading.Lock()

    def create_session(self):
        thread_id = str(uuid4())

        # Generate a secret with 256 bits of entropy.
        token = secrets.token_urlsafe(32)

        token_hash = hashlib.sha256(
            token.encode("utf-8")
        ).digest()

        session = AnalysisSession(
            token_hash=token_hash,
            expires_at=time.monotonic() + self.ttl,
        )

        with self.lock:
            self.sessions[thread_id] = session

        return thread_id, token

    @contextmanager
    def authorize(self, thread_id, token):
        with self.lock:
            session = self.sessions.get(thread_id)

            if session is None:
                raise HTTPException(
                    status_code=404,
                    detail="Analysis not found or expired",
                )

            # Keep cleanup from deleting an active workflow.
            session.lock.acquire()

        try:
            if time.monotonic() >= session.expires_at:
                raise HTTPException(
                    status_code=404,
                    detail="Analysis not found or expired",
                )

            supplied_hash = hashlib.sha256(
                token.encode("utf-8")
            ).digest()

            if not hmac.compare_digest(
                supplied_hash,
                session.token_hash,
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Analysis not found or expired",
                )

            yield

        finally:
            session.lock.release()

    def delete_session(self, thread_id):
        with self.lock:
            session = self.sessions.get(thread_id)

            if session is None:
                return

            session.lock.acquire()

            try:
                self.sessions.pop(thread_id, None)

                # Remove LangGraph checkpoints containing
                # resume and job description data.
                self.checkpointer.delete_thread(thread_id)

            finally:
                session.lock.release()

    def cleanup_expired(self):
        deleted = 0

        with self.lock:
            now = time.monotonic()

            for thread_id, session in list(
                self.sessions.items()
            ):
                if now < session.expires_at:
                    continue

                # Do not interrupt an active analysis.
                if not session.lock.acquire(blocking=False):
                    continue

                try:
                    self.sessions.pop(thread_id, None)

                    self.checkpointer.delete_thread(
                        thread_id
                    )

                    deleted += 1

                finally:
                    session.lock.release()

        return deleted
