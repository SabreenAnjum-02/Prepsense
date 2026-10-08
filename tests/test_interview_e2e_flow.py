import pytest
import asyncio
from fastapi.testclient import TestClient
from api.app import app


@pytest.mark.asyncio
async def test_interview_e2e_first_turn():
    client = TestClient(app)

    # 1. Candidate creates assessment (guest intake flow)
    create_payload = {
        "candidate_name": "Sabreen",
        "candidate_email": "sabreen@example.com",
        "target_role": "Backend Engineer",
        "skills": ["Python", "FastAPI"],
        "experience_years": 3,
        "projects": ["REST API", "Database Migration"],
        "experience": ["3 years at TechCorp"],
        "job_description": "We need a Python Backend Engineer with FastAPI experience."
    }
    create_res = client.post("/api/assessment/create", json=create_payload)
    assert create_res.status_code == 200
    create_data = create_res.json()
    session_id = create_data["session_id"]
    interview_token = create_data["interview_token"]
    assert session_id
    assert interview_token
    print(f"\n[E2E] Session Created: {session_id}")
    print(f"[E2E] Interview Token: {interview_token[:25]}...")

    # 2. Connect WebSocket using interview credential
    with client.websocket_connect(f"/api/ws/interview/{session_id}/audio?token={interview_token}") as ws:
        init_msg = ws.receive_json()
        assert init_msg.get("type") in ["state", "question"]
        print(f"[E2E] WebSocket Handshake Accepted: initial message {init_msg}")

        # 3. Trigger interview start
        start_res = client.post(f"/api/assessment/{session_id}/start")
        assert start_res.status_code == 200
        print("[E2E] Start Interview endpoint called successfully")

        # 4. Wait for Question and TTS audio chunks
        received_question = False
        received_audio_bytes = 0
        total_chunks = 0

        for _ in range(50):
            try:
                # Poll message with timeout
                msg = ws.receive()
                if "text" in msg:
                    import json
                    data = json.loads(msg["text"])
                    print(f"[E2E] WS Event received: {data.get('type')} - {data.get('state', '')}")
                    if data.get("type") == "question":
                        received_question = True
                        print(f"[E2E] AI Question Generated: {data.get('text')}")
                elif "bytes" in msg:
                    chunk = msg["bytes"]
                    received_audio_bytes += len(chunk)
                    total_chunks += 1
                    if total_chunks % 5 == 0:
                        print(f"[E2E] Received {total_chunks} TTS audio chunks ({received_audio_bytes} bytes total)")
                
                # If we received question and at least some audio chunks
                if received_question and total_chunks > 0:
                    break
            except Exception as e:
                print(f"[E2E] Poll timeout/error: {e}")
                break

        assert received_question, "Failed to receive generated interview question over WebSocket"
        assert received_audio_bytes > 0, "Failed to receive Kokoro TTS audio chunks over WebSocket"
        print(f"\n[E2E] SUCCESS: First AI Turn completely verified! Question received & {received_audio_bytes} bytes of TTS streamed.")
