
"""Integration tests for anonymous FastAPI session security."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from resume_analyzer import api
from resume_analyzer.sessions import SessionStore


class FakeGraph:
    """Replace real LangGraph execution during tests."""

    def __init__(self):
        self.states = {}
        self.invoke_count = 0

    def invoke(self, data, config):
        self.invoke_count += 1

        thread_id = config["configurable"]["thread_id"]

        # Simulate starting a new analysis.
        if isinstance(data, dict):
            self.states[thread_id] = SimpleNamespace(
                values={
                    "match_score": 85.0,
                    "hard_gaps": [],
                    "requirement_matches": [],
                    "review_completed": False,
                },
                next=("human_review",),
            )

            return {
                "__interrupt__": [
                    SimpleNamespace(
                        value={"message": "Review your analysis"}
                    )
                ]
            }

        # Simulate completing a human review.
        self.states[thread_id] = SimpleNamespace(
            values={
                "match_score": 85.0,
                "hard_gaps": [],
                "requirement_matches": [],
                "review_completed": True,
            },
            next=(),
        )

        return {}

    def get_state(self, config):
        thread_id = config["configurable"]["thread_id"]

        return self.states.get(
            thread_id,
            SimpleNamespace(values={}, next=()),
        )


class FakeCheckpointer:
    def __init__(self, graph):
        self.graph = graph
        self.deleted = []

    def delete_thread(self, thread_id):
        self.deleted.append(thread_id)
        self.graph.states.pop(thread_id, None)


@pytest.fixture
def test_environment(monkeypatch):
    graph = FakeGraph()
    checkpointer = FakeCheckpointer(graph)

    store = SessionStore(checkpointer)

    monkeypatch.setattr(api, "review_graph", graph)
    monkeypatch.setattr(api, "session_store", store)

    with TestClient(api.app) as client:
        yield client, graph, store, checkpointer


def start_analysis(client):
    response = client.post(
        "/analyses",
        json={
            "resume": "Python developer with FastAPI experience.",
            "job_description": "Seeking Python developer.",
        },
    )

    assert response.status_code == 200
    return response.json()


def test_health_endpoint(test_environment):
    client, _, _, _ = test_environment

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analysis_creates_secure_session(test_environment):
    client, _, _, _ = test_environment

    result = start_analysis(client)

    assert "thread_id" in result
    assert "session_token" in result
    assert len(result["session_token"]) >= 32
    assert result["status"] == "paused"


def test_missing_token_rejected(test_environment):
    client, graph, _, _ = test_environment
    result = start_analysis(client)
    before = graph.invoke_count

    response = client.post(
        f"/analyses/{result['thread_id']}/review",
        json={},
    )

    assert response.status_code in (401, 422)
    assert graph.invoke_count == before


def test_invalid_token_rejected(test_environment):
    client, graph, _, _ = test_environment
    result = start_analysis(client)
    before = graph.invoke_count

    response = client.post(
        f"/analyses/{result['thread_id']}/review",
        headers={
            "X-Analysis-Token": "invalid-session-token"
        },
        json={},
    )

    assert response.status_code == 404
    assert graph.invoke_count == before


def test_valid_token_accepted(test_environment):
    client, graph, _, _ = test_environment
    result = start_analysis(client)

    response = client.post(
        f"/analyses/{result['thread_id']}/review",
        headers={
            "X-Analysis-Token": result["session_token"]
        },
        json={
            "reviews": [],
            "additional_information": [],
            "approved_for_optimization": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["review_completed"] is True
    assert graph.invoke_count == 2


def test_cross_session_access_rejected(test_environment):
    client, graph, _, _ = test_environment

    first = start_analysis(client)
    second = start_analysis(client)
    before = graph.invoke_count

    response = client.post(
        f"/analyses/{first['thread_id']}/review",
        headers={
            "X-Analysis-Token": second["session_token"]
        },
        json={},
    )

    assert response.status_code == 404
    assert graph.invoke_count == before


def test_expired_token_rejected(test_environment):
    client, graph, store, checkpointer = test_environment

    result = start_analysis(client)
    before = graph.invoke_count

    # Expire the session without waiting 15 minutes.
    store.sessions[result["thread_id"]].expires_at = 0

    response = client.post(
        f"/analyses/{result['thread_id']}/review",
        headers={
            "X-Analysis-Token": result["session_token"]
        },
        json={},
    )

    assert response.status_code == 404
    assert graph.invoke_count == before

    store.cleanup_expired()

    assert result["thread_id"] in checkpointer.deleted
    assert result["thread_id"] not in graph.states


def test_unknown_analysis_rejected(test_environment):
    client, graph, _, _ = test_environment
    before = graph.invoke_count

    response = client.post(
        "/analyses/00000000-0000-0000-0000-000000000000/review",
        headers={
            "X-Analysis-Token": "some-random-token"
        },
        json={},
    )

    assert response.status_code == 404
    assert graph.invoke_count == before
