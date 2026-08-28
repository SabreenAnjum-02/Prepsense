# PrepSense: Autonomous AI Technical Interview Platform

PrepSense is a full-stack, enterprise-grade AI technical interview platform designed to autonomously conduct adaptive technical interviews, evaluate multi-turn candidate responses, assess practical coding skills in a sandbox, and generate comprehensive hiring reports.

---

## 🌟 Key Architecture & Features

### 1. Multi-Agent Autonomous Orchestration
- **Interviewer Agent:** Dynamically formulates context-grounded questions and follow-ups.
- **Evaluator Agent:** Performs real-time multi-dimensional scoring (Technical accuracy, communication, problem-solving, depth).
- **Planner Agent:** Dynamically adapts interview stage, topic transitions, and difficulty progression based on live candidate performance.
- **Resume Profiler:** Extracts structured competencies, skills, and experience to personalize question blueprints.
- **Memory Agent:** Maintains persistent conversational context, performance history, and cross-turn references.
- **Practical Sandbox Evaluator:** Automated test-case execution engine for practical coding challenges.
- **Report Generator:** Synthesizes structured evaluation analytics, strengths, areas for improvement, and hiring recommendations.

### 2. Real-Time Hands-Free Voice Pipeline
- **WebSocket Protocol:** Low-latency bidirectional audio streaming at `/api/ws/interview/{session_id}/audio`.
- **Silero VAD:** Real-time Voice Activity Detection for natural hands-free turn taking and interruption handling.
- **Faster-Whisper STT:** High-precision Speech-to-Text inference (int8 CPU-optimized).
- **Kokoro TTS:** High-fidelity speech synthesis streaming with instant client interruption support.
- **Lightweight DEV_MODE:** Instantaneous development mode (`PREPSENSE_DEV_MODE=1`) for local CPU testing without loading heavy weights.

### 3. Modern Next.js 15 Frontend
- **3-Column Workspace:** Structured desktop layout featuring Interview Progress, Primary AI Interaction, and Live Transcript/Insights.
- **Dynamic AI Avatar:** State-aware animated visualizer for Listening, Thinking, Speaking, and Idle modes.
- **Zero-Friction Audio:** Automatic microphone streaming with resilient exponential-backoff session reconnection.

### 4. Resilient Persistence & Fault Tolerance
- **Hybrid Storage Engine:** Production PostgreSQL (asyncpg) + Redis cache with transparent, zero-config SQLite/Durable fallback.
- **Session Recovery:** Idempotent state recovery allowing seamless resumption of in-progress interviews across network drops.

---

## 📁 Repository Structure

```
Prepsense/
├── agents/                  # Multi-agent implementations (Interviewer, Evaluator, Planner, etc.)
│   ├── interviewer/        # Conversational dialogue manager & question generator
│   ├── evaluator/          # Multi-criteria scoring & evaluation
│   ├── planner/            # Adaptive stage & difficulty planning
│   ├── memory/             # Candidate & session memory state
│   ├── resume/             # Resume parsing & profiler
│   ├── report/             # Final evaluation report synthesis
│   └── sandbox/            # Practical code execution runner
├── api/                    # FastAPI REST API & WebSocket endpoints
│   ├── app.py              # Main application entrypoint
│   ├── routes.py           # Assessment & resume endpoints
│   ├── voice_ws.py         # Voice WebSocket streaming handler
│   └── session_manager.py  # Session lifecycle & persistence coordinator
├── database/               # PostgreSQL & SQLite persistence layer
├── voice/                  # STT, TTS, and VAD audio wrappers
├── web/                    # Next.js 15 React frontend
│   ├── src/app/            # App router pages (intake, interview, practical, report)
│   └── src/components/     # UI components (Avatar, Candidate Camera, etc.)
├── tests/                  # Pytest test suite (unit, integration, voice hardening)
├── alembic/                # Database schema migrations
└── requirements.txt        # Python dependency declarations
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ (Recommended: 3.11 / 3.12 / 3.13)
- Node.js 18+ & npm

---

### Backend Setup

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Backend:**
   - **For Development (Lightweight CPU mode):**
     ```powershell
     $env:PREPSENSE_DEV_MODE="1"
     python -m uvicorn api.app:app --host 0.0.0.0 --port 8000
     ```
   - **For Production (Full AI Models):**
     ```bash
     python -m uvicorn api.app:app --host 0.0.0.0 --port 8000
     ```

---

### Frontend Setup

1. **Navigate to the web directory and install dependencies:**
   ```bash
   cd web
   npm install
   ```

2. **Run the Development Server:**
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

3. **Production Build:**
   ```bash
   npm run build
   npm run start
   ```

---

## 🧪 Testing & Verification

Run the full automated test suite:
```bash
python -m pytest tests/ -v
```

Run voice hardening and model lifecycle checks:
```bash
python -m pytest tests/test_model_lifecycle.py tests/test_phase5_voice.py tests/test_voice_hardening.py -v
```

---

## 📄 License

PrepSense is licensed under the MIT License.
