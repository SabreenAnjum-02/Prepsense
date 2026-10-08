import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from api.app import app
from api.auth import create_interview_token
from api.session_manager import SessionManager


@pytest.mark.asyncio
async def test_websocket_security_all_cases():
    session_mgr = SessionManager()
    
    # Create two distinct legitimate sessions
    session_a = await session_mgr.create_session(
        candidate_name="Alice Candidate",
        candidate_email="alice@example.com",
        target_role="Software Engineer",
        skills=["Python", "FastAPI"]
    )
    session_b = await session_mgr.create_session(
        candidate_name="Bob Candidate",
        candidate_email="bob@example.com",
        target_role="Frontend Engineer",
        skills=["React", "TypeScript"]
    )

    token_a = create_interview_token(session_a, "alice@example.com")
    token_b = create_interview_token(session_b, "bob@example.com")
    expired_token = create_interview_token(session_a, "alice@example.com", expires_delta=timedelta(seconds=-10))

    client = TestClient(app)

    # TEST 1: Legitimate guest: valid session_id + valid matching interview credential -> CONNECTED
    with client.websocket_connect(f"/api/ws/interview/{session_a}/audio?token={token_a}") as ws:
        msg = ws.receive_json()
        assert msg.get("type") in ["state", "question"]
        print("\nTEST 1 PASSED: Legitimate guest accepted (CONNECTED)")

    # TEST 2: Missing credential: valid session_id + no credential -> REJECTED
    try:
        with client.websocket_connect(f"/api/ws/interview/{session_a}/audio") as ws:
            pytest.fail("Expected WebSocket to be rejected when token is missing")
    except WebSocketDisconnect as e:
        assert e.code == 4001
        print("TEST 2 PASSED: Missing credential rejected with 4001")

    # TEST 3: Random credential: valid session_id + invalid credential -> REJECTED
    try:
        with client.websocket_connect(f"/api/ws/interview/{session_a}/audio?token=invalid.jwt.token") as ws:
            pytest.fail("Expected WebSocket to be rejected for invalid token")
    except WebSocketDisconnect as e:
        assert e.code == 4001
        print("TEST 3 PASSED: Random/invalid credential rejected with 4001")

    # TEST 4: Session A + Session B's credential -> REJECTED
    try:
        with client.websocket_connect(f"/api/ws/interview/{session_a}/audio?token={token_b}") as ws:
            pytest.fail("Expected WebSocket to be rejected for cross-session token")
    except WebSocketDisconnect as e:
        assert e.code == 4001
        print("TEST 4 PASSED: Cross-session credential rejected with 4001")

    # TEST 5: Expired credential -> REJECTED
    try:
        with client.websocket_connect(f"/api/ws/interview/{session_a}/audio?token={expired_token}") as ws:
            pytest.fail("Expected WebSocket to be rejected for expired token")
    except WebSocketDisconnect as e:
        assert e.code == 4001
        print("TEST 5 PASSED: Expired credential rejected with 4001")

    # TEST 6: A completely random/nonexistent session_id -> REJECTED
    fake_session_id = "00000000-0000-0000-0000-000000000000"
    fake_token = create_interview_token(fake_session_id, "fake@example.com")
    try:
        with client.websocket_connect(f"/api/ws/interview/{fake_session_id}/audio?token={fake_token}") as ws:
            pytest.fail("Expected WebSocket to be rejected for nonexistent session")
    except WebSocketDisconnect as e:
        assert e.code == 4001
        print("TEST 6 PASSED: Nonexistent session rejected with 4001")
