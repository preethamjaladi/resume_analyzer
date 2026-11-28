
"""Integration tests for Resume Analyzer API security.

Tests:
- Health endpoint
- Anonymous session creation
- Missing and invalid session tokens
- Valid session authorization
- Cross-session access isolation
- Session expiration and checkpoint deletion
- Unknown analysis rejection
- API rate limiting
- Groq rate-limit error handling
- Unexpected workflow error cleanup

No real Groq API requests are made.
"""

from types import SimpleNamespace

import httpx
import pytest

from fastapi.testclient import TestClient
from groq import RateLimitError

from resume_analyzer import api
from resume_analyzer.sessions import SessionStore
from resume_analyzer.rate_limiter import AnalysisRateLimiter

# FAKE LANGGRAPH

class FakeGraph:
    """Simulate LangGraph without calling Groq."""

    def __init__(self):
        self.states = {}
        self.invoke_count = 0

    def invoke(self, data, config):
        self.invoke_count += 1

        thread_id = config["configurable"]["thread_id"]

        # Initial analysis
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
                        value={
                            "message": "Review your analysis"
                        }
                    )
                ]
            }

        # Human review completed
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
            SimpleNamespace(
                values={},
                next=(),
            ),
        )


# FAKE CHECKPOINTER

class FakeCheckpointer:
    """Track checkpoint deletion during tests."""

    def __init__(self, graph):
        self.graph = graph
        self.deleted = []

    def delete_thread(self, thread_id):
        self.deleted.append(thread_id)
        self.graph.states.pop(thread_id, None)

# TEST FIXTURE

@pytest.fixture
def test_environment(monkeypatch):

    graph = FakeGraph()
    checkpointer = FakeCheckpointer(graph)

    store = SessionStore(checkpointer)

    limiter = AnalysisRateLimiter(
        max_requests=30,
        window_seconds=3600,
        max_concurrent=2,
    )

    # Replace real dependencies with test doubles.
    monkeypatch.setattr(
        api,
        "review_graph",
        graph,
    )

    monkeypatch.setattr(
        api,
        "session_store",
        store,
    )

    monkeypatch.setattr(
        api,
        "analysis_limiter",
        limiter,
    )

    # Return HTTP 500 instead of re-raising exceptions.
    with TestClient(
        api.app,
        raise_server_exceptions=False,
    ) as client:
        yield client, graph, store, checkpointer

# HELPER

def start_analysis(client):

    response = client.post(
        "/analyses",
        json={
            "resume": (
                "Python developer with FastAPI experience."
            ),
            "job_description": (
                "Seeking Python developer."
            ),
        },
    )

    assert response.status_code == 200

    return response.json()

# TEST 1: HEALTH ENDPOINT

def test_health_endpoint(test_environment):

    client, _, _, _ = test_environment

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# TEST 2: SECURE SESSION CREATION

def test_analysis_creates_secure_session(test_environment):

    client, _, _, _ = test_environment

    result = start_analysis(client)

    assert "thread_id" in result
    assert "session_token" in result
    assert len(result["session_token"]) >= 32
    assert result["status"] == "paused"

# TEST 3: MISSING TOKEN

def test_missing_token_rejected(test_environment):

    client, graph, _, _ = test_environment

    result = start_analysis(client)

    before = graph.invoke_count

    response = client.post(
        f"/analyses/{result['thread_id']}/review",
        json={},
    )

    assert response.status_code in (401, 422)

    # Unauthorized request must not execute LangGraph.
    assert graph.invoke_count == before

# TEST 4: INVALID TOKEN

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

# TEST 5: VALID TOKEN

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

    # Initial analysis + human review.
    assert graph.invoke_count == 2

# TEST 6: CROSS-SESSION ACCESS

def test_cross_session_access_rejected(test_environment):

    client, graph, _, _ = test_environment

    first = start_analysis(client)
    second = start_analysis(client)

    before = graph.invoke_count

    # Try accessing first session using second session's token.
    response = client.post(
        f"/analyses/{first['thread_id']}/review",
        headers={
            "X-Analysis-Token": second["session_token"]
        },
        json={},
    )

    assert response.status_code == 404
    assert graph.invoke_count == before

# TEST 7: SESSION EXPIRATION

def test_expired_token_rejected(test_environment):

    client, graph, store, checkpointer = test_environment

    result = start_analysis(client)

    before = graph.invoke_count

    # Simulate expiration without waiting 15 minutes.
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

# TEST 8: UNKNOWN ANALYSIS

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

# TEST 9: API RATE LIMIT

def test_api_rate_limit_blocks_graph(
    test_environment,
    monkeypatch,
):

    client, graph, _, _ = test_environment

    limiter = AnalysisRateLimiter(
        max_requests=1,
        window_seconds=3600,
        max_concurrent=1,
    )

    monkeypatch.setattr(
        api,
        "analysis_limiter",
        limiter,
    )

    payload = {
        "resume": "Python developer",
        "job_description": "Python experience required",
    }

    first = client.post(
        "/analyses",
        json=payload,
    )

    assert first.status_code == 200
    assert graph.invoke_count == 1

    second = client.post(
        "/analyses",
        json=payload,
    )

    assert second.status_code == 429

    # Rate-limited request must not invoke LangGraph.
    assert graph.invoke_count == 1

# TEST 10: GROQ RATE LIMIT ERROR

def test_groq_rate_limit_returns_503(
    test_environment,
    monkeypatch,
):

    client, graph, store, checkpointer = test_environment

    def raise_groq_rate_limit(data, config):

        request = httpx.Request(
            "POST",
            "https://api.groq.com/openai/v1/chat/completions",
        )

        response = httpx.Response(
            429,
            request=request,
            headers={
                "retry-after": "9"
            },
            json={
                "error": {
                    "message": "Token limit exceeded"
                }
            },
        )

        raise RateLimitError(
            "Token limit exceeded",
            response=response,
            body=None,
        )

    monkeypatch.setattr(
        graph,
        "invoke",
        raise_groq_rate_limit,
    )

    response = client.post(
        "/analyses",
        json={
            "resume": "Python developer",
            "job_description": "Python required",
        },
    )

    assert response.status_code == 503
    assert response.headers["retry-after"] == "9"

    assert "temporary usage limit" in (
        response.json()["detail"]
    )

    # Failed sessions must be removed.
    assert len(store.sessions) == 0

    # LangGraph checkpoint cleanup must run.
    assert len(checkpointer.deleted) == 1

    # Never expose a session secret on errors.
    assert "session_token" not in response.json()

# TEST 11: UNEXPECTED GRAPH ERROR

def test_unexpected_graph_error_cleans_session(
    test_environment,
    monkeypatch,
):

    client, graph, store, checkpointer = test_environment

    def raise_error(data, config):
        raise RuntimeError(
            "Simulated workflow failure"
        )

    monkeypatch.setattr(
        graph,
        "invoke",
        raise_error,
    )

    response = client.post(
        "/analyses",
        json={
            "resume": "Python developer",
            "job_description": "Python required",
        },
    )

    # TestClient returns 500 instead of raising the exception.
    assert response.status_code == 500

    # Session metadata must be deleted.
    assert len(store.sessions) == 0

    # Associated LangGraph checkpoint must be deleted.
    assert len(checkpointer.deleted) == 1
