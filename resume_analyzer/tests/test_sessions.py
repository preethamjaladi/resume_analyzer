
import time

import pytest
from fastapi import HTTPException

from resume_analyzer.sessions import SessionStore


class FakeCheckpointer:
    def __init__(self):
        self.deleted = []

    def delete_thread(self, thread_id):
        self.deleted.append(thread_id)


def test_valid_session():
    store = SessionStore(FakeCheckpointer())

    thread_id, token = store.create_session()

    with store.authorize(thread_id, token):
        pass


def test_invalid_token_rejected():
    store = SessionStore(FakeCheckpointer())

    thread_id, _ = store.create_session()

    with pytest.raises(HTTPException) as exc:
        with store.authorize(thread_id, "invalid-token"):
            pass

    assert exc.value.status_code == 404


def test_cross_session_access_rejected():
    store = SessionStore(FakeCheckpointer())

    first_id, first_token = store.create_session()
    second_id, second_token = store.create_session()

    with pytest.raises(HTTPException):
        with store.authorize(first_id, second_token):
            pass

    with store.authorize(first_id, first_token):
        pass

    with store.authorize(second_id, second_token):
        pass


def test_session_expiration_deletes_checkpoint():
    checkpointer = FakeCheckpointer()

    store = SessionStore(
        checkpointer,
        ttl=0.05,
    )

    thread_id, token = store.create_session()

    time.sleep(0.08)

    with pytest.raises(HTTPException):
        with store.authorize(thread_id, token):
            pass

    deleted = store.cleanup_expired()

    assert deleted == 1
    assert thread_id in checkpointer.deleted
    assert thread_id not in store.sessions


def test_manual_deletion():
    checkpointer = FakeCheckpointer()
    store = SessionStore(checkpointer)

    thread_id, token = store.create_session()

    store.delete_session(thread_id)

    assert thread_id in checkpointer.deleted

    with pytest.raises(HTTPException):
        with store.authorize(thread_id, token):
            pass
